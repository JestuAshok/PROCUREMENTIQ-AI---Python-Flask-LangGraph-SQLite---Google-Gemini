/**
 * PROCUREMENTIQ AI — Vanilla JS Interactivity
 * Minimal, fast, and accessible client-side enhancements.
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Password Visibility Toggle
  const toggleButtons = document.querySelectorAll('.password-toggle-btn');
  toggleButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.getAttribute('data-target');
      const input = document.getElementById(targetId);
      if (input) {
        if (input.type === 'password') {
          input.type = 'text';
          btn.innerHTML = '<i class="bi bi-eye-slash"></i>';
        } else {
          input.type = 'password';
          btn.innerHTML = '<i class="bi bi-eye"></i>';
        }
      }
    });
  });

  // 2. Alert Dismissal
  const closeAlertButtons = document.querySelectorAll('.alert-close');
  closeAlertButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const alert = btn.closest('.alert');
      if (alert) {
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-6px)';
        alert.style.transition = 'all 0.2s ease-out';
        setTimeout(() => alert.remove(), 200);
      }
    });
  });

  // 3. Sidebar Drawer Offcanvas Toggle
  const sidebar = document.getElementById('appSidebar') || document.querySelector('.sidebar');
  const sidebarToggle = document.getElementById('sidebarToggle') || document.getElementById('mobileSidebarToggle');
  const sidebarCloseBtn = document.getElementById('sidebarCloseBtn');
  const sidebarBackdrop = document.getElementById('sidebarBackdrop');

  function openSidebar() {
    if (sidebar) {
      sidebar.classList.add('open');
      sidebar.classList.add('mobile-open');
    }
    if (sidebarBackdrop) {
      sidebarBackdrop.classList.add('active');
    }
  }

  function closeSidebar() {
    if (sidebar) {
      sidebar.classList.remove('open');
      sidebar.classList.remove('mobile-open');
    }
    if (sidebarBackdrop) {
      sidebarBackdrop.classList.remove('active');
    }
  }

  if (sidebarToggle) {
    sidebarToggle.addEventListener('click', (e) => {
      e.stopPropagation();
      if (sidebar && (sidebar.classList.contains('open') || sidebar.classList.contains('mobile-open'))) {
        closeSidebar();
      } else {
        openSidebar();
      }
    });
  }

  if (sidebarCloseBtn) {
    sidebarCloseBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      closeSidebar();
    });
  }

  if (sidebarBackdrop) {
    sidebarBackdrop.addEventListener('click', closeSidebar);
  }

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeSidebar();
    }
  });

  // 4. File Dropzone Visual Feedback
  const dropzone = document.getElementById('quotationDropzone');
  const fileInput = document.getElementById('quotationFileInput');
  const fileListDisplay = document.getElementById('selectedFilesList');

  if (dropzone && fileInput) {
    ['dragenter', 'dragover'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        dropzone.classList.add('drag-active');
      }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        dropzone.classList.remove('drag-active');
      }, false);
    });

    dropzone.addEventListener('drop', (e) => {
      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        fileInput.files = e.dataTransfer.files;
        updateFileList();
      }
    });

    fileInput.addEventListener('change', () => {
      updateFileList();
    });

    function updateFileList() {
      if (!fileListDisplay) return;
      fileListDisplay.innerHTML = '';
      const files = Array.from(fileInput.files);
      if (files.length === 0) {
        fileListDisplay.innerHTML = '<span class="text-muted">No files selected yet</span>';
        return;
      }
      files.forEach((f, idx) => {
        const item = document.createElement('div');
        item.className = 'selected-file-pill';
        const sizeKb = (f.size / 1024).toFixed(1);
        item.innerHTML = `
          <i class="bi bi-file-earmark-check"></i>
          <span>${f.name} <small class="text-muted">(${sizeKb} KB)</small></span>
        `;
        fileListDisplay.appendChild(item);
      });
    }
  }

  // 5. Vendor Comparison Modal
  const compareModal = document.getElementById('compareModal');
  const openCompareBtns = document.querySelectorAll('.open-compare-btn');
  const closeCompareBtn = document.getElementById('closeCompareBtn');

  if (compareModal) {
    openCompareBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        compareModal.classList.add('active');
      });
    });

    if (closeCompareBtn) {
      closeCompareBtn.addEventListener('click', () => {
        compareModal.classList.remove('active');
      });
    }

    compareModal.addEventListener('click', (e) => {
      if (e.target === compareModal) {
        compareModal.classList.remove('active');
      }
    });
  }
});
