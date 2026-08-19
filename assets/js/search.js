document.addEventListener('DOMContentLoaded', function() {
  // 搜索功能
  const searchInput = document.getElementById('search-input');
  const searchResults = document.getElementById('search-results');
  let searchIndex = [];

  if (searchInput) {
    // 加载搜索索引
    fetch('/lkm/assets/search.json')
      .then(r => r.json())
      .then(data => { searchIndex = data; })
      .catch(() => {});

    searchInput.addEventListener('input', function() {
      const query = this.value.toLowerCase().trim();
      if (query.length < 2) {
        searchResults.innerHTML = '';
        return;
      }

      const results = searchIndex.filter(item =>
        item.title.toLowerCase().includes(query) ||
        (item.tags && item.tags.some(t => t.toLowerCase().includes(query))) ||
        (item.authors && item.authors.some(a => a.toLowerCase().includes(query))) ||
        item.id.toLowerCase().includes(query) ||
        (item.tldr && item.tldr.toLowerCase().includes(query))
      ).slice(0, 10);

      if (results.length === 0) {
        searchResults.innerHTML = '<div class="search-result"><span class="result-title">无匹配结果</span></div>';
        return;
      }

      searchResults.innerHTML = results.map(item =>
        `<a href="${item.url}" class="search-result">
          <span class="result-type">${item.type || ''}</span>
          <span class="result-title">${item.title}</span>
          <span class="result-date">${item.date}</span>
        </a>`
      ).join('');
    });

    // 点击外部关闭搜索结果
    document.addEventListener('click', function(e) {
      if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
        searchResults.innerHTML = '';
      }
    });
  }

  // 筛选功能
  const filterType = document.getElementById('filter-type');
  const filterStatus = document.getElementById('filter-status');
  const filterReset = document.getElementById('filter-reset');
  const cards = document.querySelectorAll('.article-card');

  if (filterType && filterStatus && cards.length > 0) {
    function applyFilters() {
      const typeVal = filterType.value;
      const statusVal = filterStatus.value;

      cards.forEach(card => {
        const matchType = !typeVal || card.dataset.type === typeVal;
        const matchStatus = !statusVal || card.dataset.status === statusVal;
        card.style.display = (matchType && matchStatus) ? '' : 'none';
      });
    }

    filterType.addEventListener('change', applyFilters);
    filterStatus.addEventListener('change', applyFilters);

    if (filterReset) {
      filterReset.addEventListener('click', function() {
        filterType.value = '';
        filterStatus.value = '';
        cards.forEach(card => card.style.display = '');
      });
    }
  }
});
