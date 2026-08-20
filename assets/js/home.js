/**
 * home.js — 首页左右分栏阅读
 * 拦截文章卡片点击 → fetch 文章 HTML → 注入右侧面板
 */
(function() {
  'use strict';

  var readPanel = document.getElementById('read-panel');
  if (!readPanel) return;

  var currentActiveCard = null;
  var currentArticleId = null;

  // ── 工具函数 ──

  function showLoading() {
    readPanel.innerHTML = '<div class="read-loading"></div>';
  }

  function showError(url, title) {
    readPanel.innerHTML =
      '<div class="read-error">' +
      '<p>文章加载失败</p>' +
      '<p><a href="' + url + '" target="_blank">直接打开 ' + (title || '文章') + '</a></p>' +
      '</div>';
  }

  function showPlaceholder() {
    readPanel.innerHTML =
      '<div class="read-placeholder">' +
      '<div class="placeholder-icon"></div>' +
      '<p>点击左侧文章卡片开始阅读</p>' +
      '</div>';
  }

  function setActiveCard(card) {
    if (currentActiveCard) currentActiveCard.classList.remove('active');
    if (card) {
      card.classList.add('active');
      currentActiveCard = card;
    }
  }

  // ── 从 fetch 的 HTML 中提取内容并渲染 ──

  function renderArticle(html, articleUrl) {
    var parser = new DOMParser();
    var doc = parser.parseFromString(html, 'text/html');

    // 提取 article-content 区域
    var articleContent = doc.querySelector('.article-content');
    if (!articleContent) {
      // 回退：尝试提取 article-page
      articleContent = doc.querySelector('.article-page');
    }
    if (!articleContent) {
      showPlaceholder();
      return;
    }

    // 注入右侧面板
    readPanel.innerHTML = '';
    readPanel.appendChild(articleContent);

    // 重新绑定文章内链接：标签链接正常跳转，文章内链接拦截
    var links = readPanel.querySelectorAll('a');
    links.forEach(function(link) {
      // 标签链接和外部链接正常跳转
      if (link.classList.contains('tag-link') || link.target === '_blank' || link.href.indexOf('lore.kernel') >= 0) {
        return;
      }
      // 站内文章链接：拦截并在右侧加载
      if (link.href.indexOf(window.location.origin) >= 0 || link.getAttribute('href').charAt(0) === '/') {
        link.addEventListener('click', function(e) {
          e.preventDefault();
          loadArticle(link.getAttribute('href'), null);
        });
      }
    });

    // 初始化 TOC（内联目录）
    initToc();

    // 滚动到顶部
    readPanel.scrollTop = 0;
  }

  // ── TOC 初始化（右侧面板内）──

  function initToc() {
    var body = readPanel.querySelector('.article-body');
    if (!body) return;

    var headings = body.querySelectorAll('h2');
    if (headings.length === 0) return;

    // 创建内联 TOC
    var tocDiv = document.createElement('div');
    tocDiv.className = 'toc-inline';
    var html = '<h4>目录</h4><ul>';
    headings.forEach(function(h) {
      var id = h.textContent.toLowerCase().replace(/[^a-z0-9\u4e00-\u9fff]+/g, '-').replace(/^-|-$/g, '');
      h.id = id;
      html += '<li><a href="#' + id + '" data-target="' + id + '">' + h.textContent + '</a></li>';
    });
    html += '</ul>';
    tocDiv.innerHTML = html;

    // 插入到 article-body 之前
    body.parentNode.insertBefore(tocDiv, body);

    // Scroll Spy
    var tocLinks = tocDiv.querySelectorAll('a[data-target]');
    if (tocLinks.length > 0) {
      var observerOptions = { root: readPanel, rootMargin: '-20px 0px -70% 0px', threshold: 0 };
      var observer = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
          if (entry.isIntersecting) {
            tocLinks.forEach(function(link) { link.classList.remove('active'); });
            var activeLink = tocDiv.querySelector('a[data-target="' + entry.target.id + '"]');
            if (activeLink) activeLink.classList.add('active');
          }
        });
      }, observerOptions);
      headings.forEach(function(h) { observer.observe(h); });
    }
  }

  // ── 加载文章 ─

  function loadArticle(url, card) {
    if (!url) return;

    // 如果点击的是已选中的卡片，不重复加载
    if (card && card === currentActiveCard) return;

    if (card) setActiveCard(card);

    showLoading();

    // 更新 URL hash
    var articleId = '';
    if (card) {
      articleId = card.getAttribute('data-article-id') || '';
    }
    if (articleId) {
      history.pushState({ articleUrl: url }, '', '#/' + articleId);
      currentArticleId = articleId;
    }

    fetch(url)
      .then(function(res) {
        if (!res.ok) throw new Error('HTTP ' + res.status);
        return res.text();
      })
      .then(function(html) {
        renderArticle(html, url);
      })
      .catch(function(err) {
        var title = card ? card.querySelector('.card-title').textContent : '';
        showError(url, title);
      });
  }

  // ── 根据 hash 加载文章 ──

  function loadFromHash() {
    var hash = window.location.hash;
    if (!hash || hash.length < 3) {
      showPlaceholder();
      return;
    }

    // hash 格式: #/article-id-slug
    var articleId = hash.substring(2); // 去掉 #/
    if (!articleId) {
      showPlaceholder();
      return;
    }

    // 查找匹配的卡片
    var cards = document.querySelectorAll('.article-card');
    for (var i = 0; i < cards.length; i++) {
      var cardId = cards[i].getAttribute('data-article-id');
      if (cardId === articleId) {
        var link = cards[i].querySelector('.article-link');
        if (link) {
          var url = link.getAttribute('data-url') || link.getAttribute('href');
          loadArticle(url, cards[i]);
          return;
        }
      }
    }

    // 未找到匹配卡片，显示 placeholder
    showPlaceholder();
  }

  // ─ 绑定卡片点击事件 ──

  function bindCardClicks() {
    var cards = document.querySelectorAll('.article-card');
    cards.forEach(function(card) {
      card.addEventListener('click', function(e) {
        // 标签链接不拦截
        if (e.target.classList.contains('tag-link')) return;

        var link = card.querySelector('.article-link');
        if (!link) return;

        e.preventDefault();
        e.stopPropagation();

        var url = link.getAttribute('data-url') || link.getAttribute('href');
        loadArticle(url, card);
      });
    });
  }

  // ── 监听前进/后退 ──

  window.addEventListener('popstate', function(e) {
    if (e.state && e.state.articleUrl) {
      loadArticle(e.state.articleUrl, null);
    } else {
      loadFromHash();
    }
  });

  // ── 初始化 ──

  bindCardClicks();
  loadFromHash();

})();
