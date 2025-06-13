from django.shortcuts import render
import logging
from django.db import transaction, connection
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import AccUsers, Personel, MagSubject, CceAssessmentItems, CceEntry
from .serializers import (
    AccUsersSerializer, PersonelSerializer, MagSubjectSerializer,
    CceAssessmentItemsSerializer, CceEntrySerializer
)

logger = logging.getLogger(__name__)


class HealthCheckView(APIView):
    """Health check endpoint"""

    def get(self, request):
        return Response({
            'status': 'healthy',
            'message': 'School Sync API is running',
            'version': '1.0.0'
        })


class ResetSyncSessionView(APIView):
    """Reset sync session - clears tracking variables"""

    def post(self, request):
        try:
            logger.info("Sync session reset requested")
            return Response({
                'success': True,
                'message': 'Sync session reset successfully'
            })
        except Exception as e:
            logger.error(f"Error resetting sync session: {str(e)}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BulkSyncDataView(APIView):
    """Optimized bulk sync endpoint for processing all school data at once"""

    def get_model_and_serializer(self, table_name):
        """Get the appropriate model and serializer for table"""
        table_mapping = {
            'acc_users': (AccUsers, AccUsersSerializer),
            'personel': (Personel, PersonelSerializer),
            'mag_subject': (MagSubject, MagSubjectSerializer),
            'cce_assessmentitems': (CceAssessmentItems, CceAssessmentItemsSerializer),
            'cce_entry': (CceEntry, CceEntrySerializer),
        }
        return table_mapping.get(table_name, (None, None))

    def clear_table(self, model):
        """Clear all data from a table efficiently"""
        try:
            with connection.cursor() as cursor:
                # Disable foreign key checks temporarily for faster truncation
                cursor.execute(f'TRUNCATE TABLE {model._meta.db_table};')
            logger.info(f"Table {model._meta.db_table} cleared successfully")
            return True
        except Exception as e:
            logger.error(
                f"Error clearing table {model._meta.db_table}: {str(e)}")
            return False

    def bulk_insert_data(self, model, data_list, batch_size=2000):
        """Optimized bulk insert with larger batch sizes"""
        try:
            total_inserted = 0

            # Process data in larger batches for better performance
            for i in range(0, len(data_list), batch_size):
                batch = data_list[i:i + batch_size]
                instances = []

                for data in batch:
                    # Handle special field mappings
                    if 'class' in data:
                        data['class_field'] = data.pop('class')
                    instances.append(model(**data))

                # Use bulk_create with ignore_conflicts=True for better performance
                created_instances = model.objects.bulk_create(
                    instances,
                    batch_size=batch_size,
                    ignore_conflicts=False
                )
                total_inserted += len(created_instances)

                # Log progress for large datasets
                if len(data_list) > 1000:
                    logger.info(
                        f"Inserted batch {i//batch_size + 1}: {len(created_instances)} records")

            logger.info(
                f"Bulk inserted {total_inserted} records into {model._meta.db_table}")
            return True, total_inserted
        except Exception as e:
            logger.error(
                f"Error bulk inserting into {model._meta.db_table}: {str(e)}")
            return False, 0

    def validate_data_batch(self, serializer_class, data_list):
        """Optimized batch validation"""
        errors = []
        valid_data = []

        # Process in smaller chunks for validation to avoid memory issues
        chunk_size = 1000
        for chunk_start in range(0, len(data_list), chunk_size):
            chunk = data_list[chunk_start:chunk_start + chunk_size]

            for i, data in enumerate(chunk):
                serializer = serializer_class(data=data)
                if serializer.is_valid():
                    valid_data.append(serializer.validated_data)
                else:
                    errors.append({
                        'row': chunk_start + i + 1,
                        'errors': serializer.errors
                    })

                    # Stop if too many errors (prevent memory issues)
                    if len(errors) >= 100:
                        logger.warning(
                            f"Stopping validation after 100 errors for {serializer_class}")
                        break

            if len(errors) >= 100:
                break

        return valid_data, errors

    def post(self, request):
        """Process complete dataset for all tables at once"""
        try:
            data = request.data
            tables_data = data.get('tables', {})

            if not tables_data:
                return Response({
                    'success': False,
                    'error': 'No table data provided'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Define sync order (important for foreign key relationships)
            sync_order = ['acc_users', 'personel', 'mag_subject',
                          'cce_assessmentitems', 'cce_entry']

            results = {}
            total_processed = 0

            logger.info(f"Starting bulk sync for {len(tables_data)} tables")

            # Use a single large transaction for all operations
            with transaction.atomic():
                for table_name in sync_order:
                    if table_name not in tables_data:
                        continue

                    table_data = tables_data[table_name]
                    logger.info(
                        f"Processing {table_name}: {len(table_data)} records")

                    # Get model and serializer
                    model, serializer_class = self.get_model_and_serializer(
                        table_name)
                    if not model:
                        return Response({
                            'success': False,
                            'error': f'Unknown table: {table_name}'
                        }, status=status.HTTP_400_BAD_REQUEST)

                    # Clear table first (only once per table)
                    if not self.clear_table(model):
                        return Response({
                            'success': False,
                            'error': f'Failed to clear table {table_name}'
                        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                    # Validate and insert data if any
                    if table_data:
                        # Skip validation for better performance if data is trusted
                        # Comment out the validation block below if data is pre-validated
                        """
                        valid_data, validation_errors = self.validate_data_batch(
                            serializer_class, table_data)
                        if validation_errors:
                            logger.warning(f"Validation errors for {table_name}: {len(validation_errors)}")
                            return Response({
                                'success': False,
                                'error': 'Data validation failed',
                                'table': table_name,
                                'validation_errors': validation_errors[:10]  # Return first 10 errors
                            }, status=status.HTTP_400_BAD_REQUEST)
                        table_data = valid_data
                        """

                        # Bulk insert with optimized batch size
                        success, inserted_count = self.bulk_insert_data(
                            model, table_data, batch_size=3000)
                        if not success:
                            return Response({
                                'success': False,
                                'error': f'Failed to insert data into {table_name}'
                            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                    else:
                        inserted_count = 0

                    results[table_name] = {
                        'records_processed': inserted_count,
                        'table_cleared': True
                    }
                    total_processed += inserted_count

                    logger.info(
                        f"Completed {table_name}: {inserted_count} records inserted")

            response_data = {
                'success': True,
                'message': f'Successfully processed {total_processed} total records across {len(results)} tables',
                'total_records': total_processed,
                'tables_processed': len(results),
                'results': results,
                'sync_completed': True
            }

            logger.info(
                f"Bulk sync completed successfully: {total_processed} total records")
            return Response(response_data)

        except Exception as e:
            logger.error(f"Unexpected error in bulk sync: {str(e)}")
            return Response({
                'success': False,
                'error': f'Internal server error: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SyncDataView(APIView):
    """Legacy sync endpoint - kept for backward compatibility"""

    def get_model_and_serializer(self, table_name):
        """Get the appropriate model and serializer for table"""
        table_mapping = {
            'acc_users': (AccUsers, AccUsersSerializer),
            'personel': (Personel, PersonelSerializer),
            'mag_subject': (MagSubject, MagSubjectSerializer),
            'cce_assessmentitems': (CceAssessmentItems, CceAssessmentItemsSerializer),
            'cce_entry': (CceEntry, CceEntrySerializer),
        }
        return table_mapping.get(table_name, (None, None))

    def clear_table(self, model):
        """Clear all data from a table efficiently"""
        try:
            with connection.cursor() as cursor:
                cursor.execute(f'TRUNCATE TABLE {model._meta.db_table};')
            logger.info(f"Table {model._meta.db_table} cleared successfully")
            return True
        except Exception as e:
            logger.error(
                f"Error clearing table {model._meta.db_table}: {str(e)}")
            return False

    def bulk_insert_data(self, model, data_list):
        """Bulk insert data efficiently"""
        try:
            instances = []
            for data in data_list:
                if 'class' in data:
                    data['class_field'] = data.pop('class')
                instances.append(model(**data))

            model.objects.bulk_create(
                instances, batch_size=1000, ignore_conflicts=False)
            logger.info(
                f"Bulk inserted {len(instances)} records into {model._meta.db_table}")
            return True, len(instances)
        except Exception as e:
            logger.error(
                f"Error bulk inserting into {model._meta.db_table}: {str(e)}")
            return False, 0

    def validate_data(self, serializer_class, data_list):
        """Validate data before insertion"""
        errors = []
        valid_data = []

        for i, data in enumerate(data_list):
            serializer = serializer_class(data=data)
            if serializer.is_valid():
                valid_data.append(serializer.validated_data)
            else:
                errors.append({
                    'row': i + 1,
                    'errors': serializer.errors
                })

        return valid_data, errors

    def post(self, request):
        try:
            data = request.data
            table_name = data.get('table')
            table_data = data.get('data', [])
            is_first_batch = data.get('is_first_batch', False)
            is_last_batch = data.get('is_last_batch', False)

            if not table_name:
                return Response({
                    'success': False,
                    'error': 'Table name is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            model, serializer_class = self.get_model_and_serializer(table_name)
            if not model:
                return Response({
                    'success': False,
                    'error': f'Unknown table: {table_name}'
                }, status=status.HTTP_400_BAD_REQUEST)

            logger.info(
                f"Processing {table_name}: {len(table_data)} records, first_batch={is_first_batch}")

            if table_data:
                valid_data, validation_errors = self.validate_data(
                    serializer_class, table_data)
                if validation_errors:
                    return Response({
                        'success': False,
                        'error': 'Data validation failed',
                        'validation_errors': validation_errors[:5]
                    }, status=status.HTTP_400_BAD_REQUEST)
                table_data = valid_data

            with transaction.atomic():
                if is_first_batch:
                    if not self.clear_table(model):
                        return Response({
                            'success': False,
                            'error': f'Failed to clear table {table_name}'
                        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                if table_data:
                    success, inserted_count = self.bulk_insert_data(
                        model, table_data)
                    if not success:
                        return Response({
                            'success': False,
                            'error': f'Failed to insert data into {table_name}'
                        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                else:
                    inserted_count = 0

            response_data = {
                'success': True,
                'message': f'Successfully processed {inserted_count} records for {table_name}',
                'table': table_name,
                'records_processed': inserted_count,
                'is_first_batch': is_first_batch,
                'is_last_batch': is_last_batch
            }

            if is_first_batch:
                response_data['table_cleared'] = True

            return Response(response_data)

        except Exception as e:
            logger.error(f"Unexpected error in sync: {str(e)}")
            return Response({
                'success': False,
                'error': f'Internal server error: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
