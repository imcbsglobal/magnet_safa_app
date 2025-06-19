/* static/school/js/main.js */

document.addEventListener("DOMContentLoaded", () => {
  // LOADING STATE
  const showLoader = () => {
    document.getElementById("globalLoader").style.display = "flex";
  };

  const hideLoader = () => {
    document.getElementById("globalLoader").style.display = "none";
  };

  //TO REDIRECT LOGINNED USER TO MARK VIEW PAGE
  const path = window.location.pathname;
  const safa_token = localStorage.getItem("safa-token");

  // Only redirect if we are at the root
  if (path === "/" || path === "") {
    if (safa_token) {
      window.location.href = "/api/school/mark-view/";
    } else {
      window.location.href = "/api/school/login-page/";
    }
    return; // Stop execution
  }
  // Logout button handler
  const logoutBtn = document.getElementById("logoutBtn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", () => {
      const confirmLogout = confirm("Are you sure you want to logout?");
      if (confirmLogout) {
        localStorage.removeItem("safa-token");
        localStorage.removeItem("safa_user_id");
        window.location.href = "/api/school/login-page/";
      }
    });
  }

  // LOGIN-PAGE JS SCRIPTs
  // DOM Elements
  const form = document.getElementById("loginForm");
  const userIdInput = document.getElementById("userId");
  const passwordInput = document.getElementById("password");
  const toggleIcon = document.getElementById("toggleIcon");
  const togglePassword = document.getElementById("togglePassword");
  const errorMessage = document.getElementById("loginError");

  // LOGIN FORM HANDLER
  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      showLoader();

      const id = userIdInput.value.trim();
      const pass = passwordInput.value;

      try {
        const response = await fetch("/api/school/login/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ id, pass }),
        });

        const data = await response.json();

        if (response.ok) {
          localStorage.setItem("safa-token", data.token);
          localStorage.setItem("safa_user_id", data.user_id);
          window.location.href = "/api/school/mark-view/";
        } else {
          errorMessage.textContent = data.error || "Login failed";
        }
      } catch (err) {
        console.error(err);
        errorMessage.textContent = "Server error";
      } finally {
        hideLoader();
      }
    });
  }

  // TOGGLE PASSWORD VISIBILITY
  if (togglePassword && passwordInput && toggleIcon) {
    togglePassword.addEventListener("click", () => {
      const isPassword = passwordInput.type === "password";
      passwordInput.type = isPassword ? "text" : "password";
      toggleIcon.classList.remove("fa-eye", "fa-eye-slash");
      toggleIcon.classList.add(isPassword ? "fa-eye-slash" : "fa-eye");
    });
  }

  // TO GET USERS NAME
  const usernameEl = document.getElementById("username");
  if (usernameEl && safa_token) {
    const user = localStorage.getItem("safa_user_id");
    usernameEl.textContent = user;
  }

  // === MARK VIEW PAGE LOGIC ===
  if (document.getElementById("marks-container")) {
    const token = localStorage.getItem("safa-token");
    const filtersEndpoint = "/api/school/filters/";
    const marksEndpoint = "/api/school/marks/";

    const filters = [
      "class_field",
      "division",
      "admission",
      "subject",
      "term",
      "part",
      "assessmentitem",
    ];

    // Pagination state
    let currentPage = 1;
    let totalPages = 1;
    let totalRecords = 0;
    let pageSize = 20;

    const fetchFilters = async () => {
      try {
        const res = await fetch(filtersEndpoint, {
          headers: { Authorization: `Bearer ${safa_token}` },
        });
        const data = await res.json();

        populateSelect("class_field", data.classes);
        populateSelect("division", data.divisions);
        populateSelect("admission", data.students, "admission", "name");
        populateSelect("subject", data.subjects, "code", "name");
        populateSelect("term", data.terms);
        populateSelect("part", data.parts);
        populateSelect("assessmentitem", data.assessment_items, "code", "name");

        // ✅ Initialize Select2 AFTER filters are populated
        $(".select2").select2({
          width: "100%",
        });
      } catch (err) {
        console.error("Error loading filters:", err);
      }
    };

    const populateSelect = (id, list, valueKey = null, textKey = null) => {
      const select = document.getElementById(id);
      if (!select) return;

      select.innerHTML = `<option value="">All</option>`;
      list.forEach((item) => {
        const option = document.createElement("option");
        option.value = valueKey ? item[valueKey] : item;
        option.textContent = textKey ? item[textKey] : item;
        select.appendChild(option);
      });
    };

    const fetchMarks = async (page = 1) => {
      const params = new URLSearchParams();

      // Add filter parameters
      filters.forEach((id) => {
        const val = document.getElementById(id)?.value;
        if (val) params.append(id, val);
      });

      // Add pagination parameters
      params.append("page", page.toString());
      params.append("page_size", pageSize.toString());

      console.log("Fetching marks with params:", params.toString());

      showLoader();

      try {
        // Show loading state
        const tbody = document.getElementById("marksTableBody");
        tbody.innerHTML = `<tr><td colspan="10" class="text-center">Loading...</td></tr>`;

        const res = await fetch(`${marksEndpoint}?${params.toString()}`, {
          headers: { Authorization: `Bearer ${safa_token}` },
        });

        const data = await res.json();
        console.log("Received marks data:", data);

        // Update pagination state
        currentPage = page;
        totalRecords = data.count || 0;
        totalPages = Math.ceil(totalRecords / pageSize);

        populateTable(data.results || []);
        updatePaginationUI();
      } catch (err) {
        console.error("Error loading marks:", err);
        const tbody = document.getElementById("marksTableBody");
        tbody.innerHTML = `<tr><td colspan="10" class="text-center">Error loading data</td></tr>`;
      } finally {
        hideLoader();
      }
    };

    const populateTable = (marks) => {
      const tbody = document.getElementById("marksTableBody");
      tbody.innerHTML = "";

      if (!marks.length) {
        tbody.innerHTML = `<tr><td colspan="10" class="text-center">No records found</td></tr>`;
        return;
      }

      marks.forEach((m) => {
        const row = document.createElement("tr");
        row.innerHTML = `
          <td>${m.admission}</td>
          <td>${m.student_name}</td>
          <td>${m.class_field}</td>
          <td>${m.division}</td>
          <td>${m.subject_name}</td>
          <td>${m.term}</td>
          <td>${m.part}</td>
          <td>${m.assessmentitem_name}</td>
          <td class="editable-mark" data-slno="${m.slno}" data-max="${
          m.maxmark
        }" data-student="${m.student_name}" data-subject="${
          m.subject_name
        }" data-class="${m.class_field}" data-division="${
          m.division
        }" data-term="${m.term}" data-part="${m.part}" data-assessment="${
          m.assessmentitem_name
        }">${m.mark !== null ? m.mark : 0}</td>
          <td>${m.grade}</td>
          <td>${m.maxmark}</td>
        `;
        tbody.appendChild(row);
      });
    };

    const updatePaginationUI = () => {
      // Update records info
      const recordsInfo = document.getElementById("recordsInfo");
      const startRecord =
        totalRecords === 0 ? 0 : (currentPage - 1) * pageSize + 1;
      const endRecord = Math.min(currentPage * pageSize, totalRecords);
      recordsInfo.textContent = `Showing ${startRecord} - ${endRecord} of ${totalRecords} records`;

      // Update total pages
      document.getElementById("totalPages").textContent = totalPages;

      // Update current page input
      document.getElementById("currentPageInput").value = currentPage;
      document.getElementById("currentPageInput").max = totalPages;

      // Update button states
      const firstPageBtn = document.getElementById("firstPage");
      const prevPageBtn = document.getElementById("prevPage");
      const nextPageBtn = document.getElementById("nextPage");
      const lastPageBtn = document.getElementById("lastPage");

      // Disable/enable buttons based on current page
      firstPageBtn.disabled = currentPage <= 1;
      prevPageBtn.disabled = currentPage <= 1;
      nextPageBtn.disabled = currentPage >= totalPages;
      lastPageBtn.disabled = currentPage >= totalPages;
    };

    const goToPage = (page) => {
      if (page < 1 || page > totalPages) return;
      fetchMarks(page);
    };

    // Event Listeners for pagination controls
    document.getElementById("firstPage")?.addEventListener("click", () => {
      goToPage(1);
    });

    document.getElementById("prevPage")?.addEventListener("click", () => {
      goToPage(currentPage - 1);
    });

    document.getElementById("nextPage")?.addEventListener("click", () => {
      goToPage(currentPage + 1);
    });

    document.getElementById("lastPage")?.addEventListener("click", () => {
      goToPage(totalPages);
    });

    // Page input handler
    document
      .getElementById("currentPageInput")
      ?.addEventListener("change", (e) => {
        const page = parseInt(e.target.value);
        if (page >= 1 && page <= totalPages) {
          goToPage(page);
        } else {
          e.target.value = currentPage; // Reset to current page if invalid
        }
      });

    // Page input on Enter key
    document
      .getElementById("currentPageInput")
      ?.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
          const page = parseInt(e.target.value);
          if (page >= 1 && page <= totalPages) {
            goToPage(page);
          } else {
            e.target.value = currentPage; // Reset to current page if invalid
          }
        }
      });

    // Page size change handler
    document.getElementById("pageSize")?.addEventListener("change", (e) => {
      pageSize = parseInt(e.target.value);
      currentPage = 1; // Reset to first page when changing page size
      fetchMarks(1);
    });

    // Filter event listeners
    document.getElementById("applyFilters")?.addEventListener("click", () => {
      currentPage = 1; // Reset to first page when applying filters
      fetchMarks(1);
    });

    document.getElementById("resetFilters")?.addEventListener("click", () => {
      filters.forEach((id) => {
        const el = document.getElementById(id);
        if (el) {
          $(el).val("").trigger("change");
        }
      });
      currentPage = 1; // Reset to first page when resetting filters
      fetchMarks(1);
    });

    // Initialize page size from select element
    const pageSizeSelect = document.getElementById("pageSize");
    if (pageSizeSelect) {
      pageSize = parseInt(pageSizeSelect.value);
    }

    // SCRIPT FOR MARK-ENTRY POPUP
    let currentSlno = null;
    let maxMark = null;

    document.addEventListener("dblclick", (e) => {
      if (e.target.classList.contains("editable-mark")) {
        const cell = e.target;
        currentSlno = cell.dataset.slno;
        maxMark = parseFloat(cell.dataset.max);

        // Fill popup with data
        document.getElementById("popupStudent").textContent =
          cell.dataset.student;
        document.getElementById("popupSubject").textContent =
          cell.dataset.subject;
        document.getElementById("popupClass").textContent = cell.dataset.class;
        document.getElementById("popupDivision").textContent =
          cell.dataset.division;
        document.getElementById("popupTerm").textContent = cell.dataset.term;
        document.getElementById("popupPart").textContent = cell.dataset.part;
        document.getElementById("popupAssessment").textContent =
          cell.dataset.assessment;
        document.getElementById("popupMax").textContent = maxMark;

        document.getElementById("popupMarkInput").value =
          cell.textContent.trim();

        document.getElementById("markPopup").style.display = "flex";
      }
    });

    document.getElementById("popupCancelBtn").addEventListener("click", () => {
      document.getElementById("markPopup").style.display = "none";
    });

    document
      .getElementById("popupSaveBtn")
      .addEventListener("click", async () => {
        const newMark = parseFloat(
          document.getElementById("popupMarkInput").value
        );

        if (isNaN(newMark) || newMark < 0 || newMark > maxMark) {
          alert(`Mark must be between 0 and ${maxMark}`);
          return;
        }

        try {
          const res = await fetch("/api/school/update-mark/", {
            method: "POST",
            headers: {
              Authorization: `Bearer ${safa_token}`,
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ slno: currentSlno, mark: newMark }),
          });

          const data = await res.json();

          if (res.ok) {
            alert("Mark updated successfully");
            document.getElementById("markPopup").style.display = "none";
            fetchMarks(currentPage); // reload data
          } else {
            alert(data.error || "Failed to update");
          }
        } catch (err) {
          alert("Server error");
          console.error(err);
        }
      });

    // Initialize the page
    fetchFilters();
    fetchMarks(1);
  }
});
