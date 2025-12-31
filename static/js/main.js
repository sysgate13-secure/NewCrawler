/**
 * @file main.js
 * @description 보안 뉴스 플랫폼의 프론트엔드 로직을 담당합니다.
 * @author Gemini
 * @date 2025-12-31
 */

// ## Region: 전역 변수 및 상수 ##
let currentSection = 'news';
let currentPage = 1;
let currentLimit = 20;
let totalPages = 1;

const CATEGORY_LABELS = {
    'malware': '악성코드', 'vulnerability': '취약점', 'network': '네트워크',
    'web': '웹 보안', 'crypto': '암호학', 'trend': '기타'
};
const CATEGORY_EMOJI = {
    'malware': '🦠', 'vulnerability': '🔓', 'network': '🌐',
    'web': '💻', 'crypto': '🔐', 'trend': '📈'
};

// ## Region: 이벤트 리스너 ##
document.addEventListener('DOMContentLoaded', () => {
    initializePagination();

    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const section = this.dataset.section;
            switchSection(section);
            document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
            this.classList.add('active');
        });
    });

    if (currentSection === 'dashboard') {
        loadDashboardData();
    }
});


// ## Region: 페이지네이션 및 데이터 로드 ##

function initializePagination() {
    const pageInfoEl = document.getElementById('pageInfo');
    const pageSizeEl = document.getElementById('pageSize');
    
    if (pageInfoEl) {
        const pageMatch = (pageInfoEl.textContent || '').match(/(\d+)\s*\/\s*(\d+)/);
        if (pageMatch) {
            currentPage = parseInt(pageMatch[1], 10);
            totalPages = parseInt(pageMatch[2], 10);
        }
    }
    if (pageSizeEl) {
        currentLimit = parseInt(pageSizeEl.value, 10);
    }
}

function changePage(direction) {
    const newPage = direction === 'prev' ? currentPage - 1 : currentPage + 1;
    if (newPage > 0 && newPage <= totalPages) {
        currentPage = newPage;
        fetchNews();
    }
}

function changeLimit(newLimit) {
    currentLimit = parseInt(newLimit, 10);
    currentPage = 1;
    fetchNews();
}

/**
 * 뉴스 데이터를 서버에서 가져와 UI를 업데이트합니다. (페이지네이션 적용)
 */
async function fetchNews() {
    const q = document.getElementById('newsSearch').value;
    const category = document.getElementById('newsCategory').value;
    const newsGrid = document.getElementById('newsGrid');
    
    newsGrid.innerHTML = '<p style="grid-column: 1/-1; text-align: center; color: #999;">로딩 중...</p>';

    try {
        const url = `/api/search?q=${encodeURIComponent(q)}&category=${encodeURIComponent(category)}&page=${currentPage}&limit=${currentLimit}&index=news`;
        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
        const data = await response.json();
        renderNews(data.news);
        updatePaginationControls(data.pagination);

    } catch (error) {
        console.error('뉴스 검색 오류:', error);
        newsGrid.innerHTML = '<p style="grid-column: 1/-1; text-align: center; color: red;">뉴스 검색 중 오류가 발생했습니다.</p>';
    }
}

/**
 * 현재 화면의 뉴스 아이템을 실시간으로 필터링합니다.
 */
function filterNews() {
    const q = document.getElementById('newsSearch').value.toLowerCase();
    const category = document.getElementById('newsCategory').value;
    const newsItems = document.querySelectorAll('#newsGrid .news-item');
    let visibleCount = 0;

    newsItems.forEach(item => {
        const title = (item.querySelector('.news-title a')?.textContent || '').toLowerCase();
        const summary = (item.querySelector('.news-summary')?.textContent || '').toLowerCase();
        const itemCategory = item.dataset.category;

        const matchesQuery = q === '' || title.includes(q) || summary.includes(q);
        const matchesCategory = category === '' || itemCategory === category;

        if (matchesQuery && matchesCategory) {
            item.style.display = 'block';
            visibleCount++;
        } else {
            item.style.display = 'none';
        }
    });

    const noResultsEl = document.getElementById('no-results-message');
    if (visibleCount === 0 && newsItems.length > 0) {
        if (!noResultsEl) {
            const el = document.createElement('p');
            el.id = 'no-results-message';
            el.textContent = '현재 페이지에 일치하는 뉴스가 없습니다.';
            el.style.cssText = 'grid-column: 1/-1; text-align: center; color: #999;';
            document.getElementById('newsGrid').appendChild(el);
        }
    } else if (noResultsEl) {
        noResultsEl.remove();
    }
}

function loadNews() {
    document.getElementById('newsSearch').value = '';
    document.getElementById('newsCategory').value = '';
    currentPage = 1;
    fetchNews();
}

// ## Region: UI 렌더링 및 업데이트 ##

function updatePaginationControls(pagination) {
    currentPage = pagination.page;
    totalPages = pagination.total_pages;

    const pageInfo = document.getElementById('pageInfo');
    const totalItems = document.getElementById('totalItems');
    const prevPageBtn = document.getElementById('prevPage');
    const nextPageBtn = document.getElementById('nextPage');

    if (pageInfo) pageInfo.textContent = `페이지 ${pagination.page} / ${pagination.total_pages}`;
    if (totalItems) totalItems.textContent = pagination.total_items;
    
    if (prevPageBtn) prevPageBtn.disabled = (pagination.page <= 1);
    if (nextPageBtn) nextPageBtn.disabled = (pagination.page >= pagination.total_pages);
}

/**
 * 뉴스 목록을 화면에 렌더링합니다.
 * @param {Array} news - 뉴스 데이터 배열
 */
function renderNews(news) {
    const newsGrid = document.getElementById('newsGrid');
    newsGrid.innerHTML = '';

    if (!news || news.length === 0) {
        newsGrid.innerHTML = '<p style="grid-column: 1/-1; text-align: center; color: #999;">표시할 뉴스가 없습니다.</p>';
        return;
    }

    news.forEach(item => {
        const newsEl = createNewsElement(item);
        newsGrid.appendChild(newsEl);
    });
}

function createNewsElement(item) {
    const newsEl = document.createElement('div');
    newsEl.className = 'news-item';
    // data-category 속성 추가
    newsEl.dataset.category = item.category || '';

    const metaEl = document.createElement('div');
    metaEl.className = 'news-meta';

    const metaDiv = document.createElement('div');
    metaDiv.style.cssText = 'display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap;';
    const catLabel = CATEGORY_LABELS[item.category] || item.category || '';
    
    const categorySpan = document.createElement('span');
    categorySpan.className = 'news-category';
    categorySpan.textContent = catLabel;

    const sourceSpan = document.createElement('span');
    sourceSpan.className = 'news-source';
    sourceSpan.textContent = `🌍 ${item.source}`;
    if (item.source && item.source.includes('보안뉴스')) {
        sourceSpan.textContent = `🇰🇷 ${item.source}`;
        sourceSpan.style.background = 'linear-gradient(135deg, #667eea, #764ba2)';
    } else {
        sourceSpan.style.background = 'linear-gradient(135deg, #f093fb, #f5576c)';
    }

    metaDiv.appendChild(categorySpan);
    metaDiv.appendChild(sourceSpan);

    const dateSpan = document.createElement('span');
    dateSpan.style.cssText = 'color: #999; font-size: 0.85rem;';
    dateSpan.textContent = item.date;

    metaEl.appendChild(metaDiv);
    metaEl.appendChild(dateSpan);

    const titleEl = document.createElement('h3');
    titleEl.className = 'news-title';
    const linkEl = document.createElement('a');
    linkEl.href = item.url;
    linkEl.target = '_blank';
    linkEl.textContent = item.title;
    titleEl.appendChild(linkEl);

    newsEl.appendChild(metaEl);
    newsEl.appendChild(titleEl);

    if (item.summary) {
        const summaryEl = document.createElement('p');
        summaryEl.className = 'news-summary';
        summaryEl.textContent = item.summary.replace(/<br\s*\/?>/gi, ' ');
        newsEl.appendChild(summaryEl);
    }
    
    const footerEl = document.createElement('div');
    footerEl.style.cssText = 'margin-top: 0.8rem; padding-top: 0.8rem; border-top: 1px solid #e9ecef; display: flex; justify-content: space-between; align-items: center;';

    const sourceInfoEl = document.createElement('div');
    sourceInfoEl.style.cssText = 'font-size: 0.8rem; color: #6c757d;';
    
    let sourceLink;
    if (item.source && item.source.includes('보안뉴스')) {
        sourceLink = '<a href="https://www.boannews.com" target="_blank" style="color: #667eea; text-decoration: none;">www.boannews.com</a>';
    } else if (item.source && item.source.includes('HackRead')) {
        sourceLink = '<a href="https://www.hackread.com" target="_blank" style="color: #f093fb; text-decoration: none;">www.hackread.com</a>';
    } else {
        sourceLink = `<span>${item.source || ''}</span>`;
    }
    sourceInfoEl.innerHTML = `📰 출처: ${sourceLink}`;
    
    const actionsEl = document.createElement('div');
    actionsEl.style.cssText = 'display: flex; align-items: center; gap: 0.5rem;';

    const viewLink = document.createElement('a');
    viewLink.href = item.url;
    viewLink.target = '_blank';
    viewLink.style.cssText = 'color: #667eea; text-decoration: none; font-size: 0.85rem; font-weight: 500;';
    viewLink.innerHTML = '원문 보기 →';

    const deleteBtn = document.createElement('button');
    deleteBtn.className = 'delete-btn';
    deleteBtn.textContent = '삭제';
    deleteBtn.onclick = () => deleteNews(item.id);

    actionsEl.appendChild(viewLink);
    actionsEl.appendChild(deleteBtn);

    footerEl.appendChild(sourceInfoEl);
    footerEl.appendChild(actionsEl);

    newsEl.appendChild(footerEl);
    
    return newsEl;
}

// ## Region: 기타 API 호출 및 유틸리티 ##

async function runCrawler() {
    if (!confirm('크롤링을 실행하시겠습니까?')) return;
    try {
        const response = await fetch('/api/crawl', { method: 'POST' });
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();
        alert(`크롤링 완료: ${data.count}개의 뉴스가 추가되었습니다.`);
        loadNews();
    } catch (error) {
        alert('크롤링 실패: ' + error.message);
    }
}

async function deleteNews(newsId) {
    if (!confirm('정말로 이 기사를 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.')) return;

    try {
        const response = await fetch(`/api/news/${newsId}`, { method: 'DELETE' });
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || '삭제에 실패했습니다.');
        }

        fetchNews(); // 삭제 후 현재 페이지 다시 로드
    } catch (error) {
        console.error('기사 삭제 중 오류 발생:', error);
        alert(`오류: ${error.message}`);
    }
}

function loadDashboardData() {
    // ...
}

function switchSection(section) {
    document.querySelectorAll('.main-container > main > div').forEach(el => {
        el.style.display = 'none';
    });
    const sectionEl = document.getElementById(section + '-section');
    if (sectionEl) sectionEl.style.display = 'block';

    currentSection = section;
    
    if (section === 'dashboard') {
        loadDashboardData();
    }
}

function filterByCategory(category) {
    document.getElementById('newsCategory').value = category;
    document.getElementById('newsSearch').value = '';
    if (currentSection !== 'news') switchSection('news');
    currentPage = 1;
    fetchNews();
}

function searchContent(query) {
    if (currentSection === 'news') {
        document.getElementById('newsSearch').value = query;
        if(query.trim() === '') document.getElementById('newsCategory').value = '';
        filterNews();
    } else if (currentSection === 'wiki') {
        searchWiki(query);
    }
}

// ... the rest of the file can remain mostly the same
async function searchWiki(query) {
     const wikiGrid = document.getElementById('wikiGrid');
     if (!wikiGrid) return;
    try {
        const url = `/api/search?q=${encodeURIComponent(query)}&index=wiki`;
        const resp = await fetch(url);
        const data = await resp.json();
        renderWikiResults(data.wiki);
    } catch (e) {
        console.error('위키 검색 오류:', e);
        wikiGrid.innerHTML = '<p>검색 중 오류가 발생했습니다.</p>';
    }
}

function renderWikiResults(wikis) {
    const wikiGrid = document.getElementById('wikiGrid');
    if (!wikiGrid) return;
    wikiGrid.innerHTML = '';
    if (!wikis || wikis.length === 0) {
        wikiGrid.innerHTML = '<p style="grid-column: 1/-1; text-align: center; color: #999;">검색 결과가 없습니다.</p>';
        return;
    }
    wikis.forEach(item => {
        const el = document.createElement('div');
        el.className = 'wiki-card';
        el.onclick = () => location.href = `/wiki/${item.id}`;

        const categoryEl = document.createElement('div');
        categoryEl.className = 'wiki-category';
        categoryEl.textContent = item.category || '';

        const titleEl = document.createElement('h3');
        titleEl.className = 'wiki-title';
        titleEl.textContent = item.title;

        if (item.preview) {
            const previewEl = document.createElement('p');
            previewEl.style.color = '#555';
            previewEl.style.fontSize = '0.9rem';
            previewEl.innerHTML = item.preview;
            el.appendChild(previewEl);
        }

        el.appendChild(categoryEl);
        el.appendChild(titleEl);

        const tagsHtml = (item.tags || '').split(',').filter(t => t).map(t => `<span style="display:inline-block;background:#eef2ff;color:#3730a3;padding:0.2rem 0.5rem;border-radius:8px;margin-right:6px;font-size:0.8rem;">#${t}</span>`).join('');
        if (tagsHtml) {
            const tagsEl = document.createElement('div');
            tagsEl.style.margin = '6px 0 0 0';
            tagsEl.innerHTML = tagsHtml;
            el.appendChild(tagsEl);
        }
        
        wikiGrid.appendChild(el);
    });
}