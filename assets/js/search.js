document.addEventListener('DOMContentLoaded', function() {
  // ── Search ──
  const searchInput = document.getElementById('search-input');
  const searchResults = document.getElementById('search-results');
  let searchIndex = [];

  if (searchInput) {
    fetch('/lkm/assets/search.json')
      .then(r => r.json())
      .then(data => { searchIndex = data; })
      .catch(() => {});

    searchInput.addEventListener('input', function() {
      const query = this.value.toLowerCase().trim();
      if (query.length < 2) { searchResults.innerHTML = ''; return; }

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

    document.addEventListener('click', function(e) {
      if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
        searchResults.innerHTML = '';
      }
    });
  }

  // ── Filters ──
  const filterType = document.getElementById('filter-type');
  const filterStatus = document.getElementById('filter-status');
  const filterSort = document.getElementById('filter-sort');
  const filterReset = document.getElementById('filter-reset');
  const filterCount = document.getElementById('filter-count');
  const btnShowAll = document.getElementById('btn-show-all');
  const allCards = document.querySelectorAll('.article-card');
  const allGroups = document.querySelectorAll('.date-group');
  const totalCards = allCards.length;

  // Update count display
  function updateCount(visible) {
    if (filterCount) {
      if (visible === totalCards) {
        filterCount.textContent = `共 ${totalCards} 篇`;
      } else {
        filterCount.textContent = `${visible} / ${totalCards} 篇`;
        filterCount.style.color = '#2563eb';
      }
    }
  }
  updateCount(totalCards);

  // Severity sort order
  const severityOrder = { critical: 0, high: 1, medium: 2, low: 3, none: 4, unknown: 5 };

  function applyFilters() {
    const typeVal = filterType ? filterType.value : '';
    const statusVal = filterStatus ? filterStatus.value : '';
    let visible = 0;

    allCards.forEach(card => {
      const matchType = !typeVal || card.dataset.type === typeVal;
      const matchStatus = !statusVal || card.dataset.status === statusVal;
      if (matchType && matchStatus) {
        card.classList.remove('filtered-out');
        visible++;
      } else {
        card.classList.add('filtered-out');
      }
    });

    // Show parent date groups if they have visible cards
    allGroups.forEach(group => {
      const visibleCards = group.querySelectorAll('.article-card:not(.filtered-out)');
      if (visibleCards.length === 0) {
        group.style.display = 'none';
      } else {
        group.style.display = '';
      }
    });

    updateCount(visible);
  }

  if (filterType) filterType.addEventListener('change', applyFilters);
  if (filterStatus) filterStatus.addEventListener('change', applyFilters);

  if (filterReset) {
    filterReset.addEventListener('click', function() {
      if (filterType) filterType.value = '';
      if (filterStatus) filterStatus.value = '';
      if (filterSort) filterSort.value = 'date-desc';
      allCards.forEach(card => card.classList.remove('filtered-out'));
      allGroups.forEach(group => group.style.display = '');
      updateCount(totalCards);
    });
  }

  // ── Show all / collapse ──
  if (btnShowAll) {
    btnShowAll.addEventListener('click', function() {
      const collapsed = document.querySelectorAll('.date-group-collapsed');
      collapsed.forEach(g => g.classList.add('show-all'));
      this.style.display = 'none';
    });
  }
});
