
document.addEventListener('alpine:init', () => {
  // 글로벌 Alpine 상태 및 이벤트 설정
  Alpine.data('adminApp', () => ({
    // 삭제 모달 관련
    deleteModal: {
      open: false,
      name: '',
      pk: '',
      url: '',
      text: '',

      // 모달 열기
      openModal(name, pk, url) {
        this.name = name;
        this.pk = pk;
        this.url = url;
        this.text = `This will permanently delete ${name} ${pk}?`;
        this.open = true;
      },

      // 삭제 수행
      confirmDelete() {
        fetch(this.url, {
          method: 'DELETE',
        })
        .then(response => response.text())
        .then(result => {
          window.location.href = result;
        })
        .catch(error => {
          alert(error);
        });
      }
    },

    // 검색 관련
    search: {
      term: '',
      timeout: null,

      // 검색 수행
      doSearch() {
        const searchTerm = encodeURIComponent(this.term);
        let newUrl = '';

        if (window.location.search && window.location.search.indexOf('search=') != -1) {
          newUrl = window.location.search.replace(/search=[^&]*/, "search=" + searchTerm);
        } else if (window.location.search) {
          newUrl = window.location.search + "&search=" + searchTerm;
        } else {
          newUrl = window.location.search + "?search=" + searchTerm;
        }
        window.location.href = newUrl;
      },

      // 자동 검색(타이핑 후 지연 시간 적용)
      autoSearch() {
        clearTimeout(this.timeout);
        this.timeout = setTimeout(() => {
          this.doSearch();
        }, 1000);
      },

      // 검색 초기화
      resetSearch() {
        if (window.location.search && window.location.search.indexOf('search=') != -1) {
          window.location.href = window.location.search.replace(/search=[^&]*/, "");
        }
      }
    },

    // 체크박스 선택 관련
    selection: {
      selectAll: false,
      selectedItems: [],

      // 전체 선택 토글
      toggleSelectAll() {
        document.querySelectorAll('.select-box').forEach(checkbox => {
          checkbox.checked = this.selectAll;
        });

        this.updateSelectedItems();
      },

      // 선택된 항목 업데이트
      updateSelectedItems() {
        this.selectedItems = [];
        document.querySelectorAll('.select-box:checked').forEach(checkbox => {
          const pk = checkbox.closest('tr').querySelector('input[type=hidden]').value;
          this.selectedItems.push(pk);
        });
      },

      // 대량 삭제 액션
      bulkDelete(url) {
        if (this.selectedItems.length === 0) {
          alert('Please select items to delete.');
          return;
        }

        const deleteUrl = url + '?pks=' + this.selectedItems.join(',');
        this.$dispatch('open-modal', {
          name: 'delete-modal',
          data: {
            name: 'selected items',
            pk: '',
            url: deleteUrl,
            text: `This will permanently delete ${this.selectedItems.length} selected items.`
          }
        });
      },

      // 커스텀 액션 수행
      customAction(url) {
        if (this.selectedItems.length === 0) {
          alert('Please select items.');
          return;
        }

        window.location.href = url + '?pks=' + this.selectedItems.join(',');
      }
    }
  }));
});

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', function() {
  // 날짜 선택기 초기화 (Flatpickr)
  initDatepickers();

  // Select2 초기화
  initSelect2();

  // URL에서 검색어 가져와서 입력 필드에 설정
  const urlParams = new URLSearchParams(window.location.search);
  const searchTerm = urlParams.get('search');

  if (searchTerm) {
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
      searchInput.value = searchTerm;
    }
  }
});

// Flatpickr 날짜 선택기 초기화
function initDatepickers() {
  // 표준 날짜 선택기
  document.querySelectorAll('input[data-role="datepicker"]:not([readonly])').forEach(element => {
    flatpickr(element, {
      enableTime: false,
      allowInput: true,
      dateFormat: "Y-m-d",
    });
  });

  // 날짜시간 선택기
  document.querySelectorAll('input[data-role="datetimepicker"]:not([readonly])').forEach(element => {
    flatpickr(element, {
      enableTime: true,
      allowInput: true,
      enableSeconds: true,
      time_24hr: true,
      dateFormat: "Y-m-d H:i:s",
    });
  });
}

// Select2 초기화
function initSelect2() {
  // 일반 Select2 (AJAX가 아닌 경우)
  document.querySelectorAll('select.select2:not([data-ajax-url])').forEach(element => {
    $(element).select2({
      theme: "classic",
      width: "100%",
    });
  });

  // AJAX Select2 (외래키 필드)
  document.querySelectorAll('select[data-ajax-url]').forEach(element => {
    $(element).select2({
      theme: "classic",
      width: "100%",
      ajax: {
        url: element.dataset.ajaxUrl,
        dataType: 'json',
        delay: 250,
        minimumInputLength: parseInt(element.dataset.minimumInputLength) || 1,
        data: function(params) {
          return {
            term: params.term,
            page: params.page || 1
          };
        },
        processResults: function(data) {
          return {
            results: data.results.map(function(item) {
              return {
                id: item[0],
                text: item[1]
              };
            }),
            pagination: {
              more: data.pagination && data.pagination.more
            }
          };
        }
      },
      placeholder: element.dataset.placeholder || "선택하세요...",
      allowClear: true
    });
  });
}

// 삭제 모달 이벤트 핸들러 (Alpine.js를 사용하지 않는 경우를 위한 백업)
document.addEventListener('click', function(event) {
  // 삭제 버튼 클릭 처리
  if (event.target.matches('[data-delete-button]') || event.target.closest('[data-delete-button]')) {
    event.preventDefault();

    const button = event.target.matches('[data-delete-button]')
      ? event.target
      : event.target.closest('[data-delete-button]');

    const name = button.dataset.name;
    const pk = button.dataset.pk;
    const url = button.dataset.url;

    // Alpine.js 컴포넌트가 있는지 확인
    const alpineComponent = document.querySelector('[x-data]').__x;
    if (alpineComponent) {
      alpineComponent.$data.deleteModal.openModal(name, pk, url);
    } else {
      // 폴백: 기본 confirm 사용
      if (confirm(`This will permanently delete ${name} ${pk}?`)) {
        fetch(url, {
          method: 'DELETE',
        })
        .then(response => response.text())
        .then(result => {
          window.location.href = result;
        })
        .catch(error => {
          alert(error);
        });
      }
    }
  }
});