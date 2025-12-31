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

    // 페이지 로드 시 초기 섹션에 맞는 데이터 로드
    if (currentSection === 'dashboard') {
        loadDashboardData();
    } else if (currentSection === 'news') {
        // 초기 뉴스 로드는 HTML에 이미 렌더링되어 있음
    }
});


// ## Region: 페이지네이션 및 데이터 로드 ##

/**
 * 페이지 로드 시 초기 페이지네이션 상태를 설정합니다.
 */
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

/**
 * 페이지를 변경합니다.
 * @param {'prev' | 'next'} direction - 변경 방향
 */
function changePage(direction) {
    const newPage = direction === 'prev' ? currentPage - 1 : currentPage + 1;
    if (newPage > 0 && newPage <= totalPages) {
        currentPage = newPage;
        searchNews();
    }
}

/**
 * 페이지당 항목 수를 변경합니다.
 * @param {string | number} newLimit - 새로운 항목 수
 */
function changeLimit(newLimit) {
    currentLimit = parseInt(newLimit, 10);
    currentPage = 1; // 항목 수가 바뀌면 1페이지부터 다시 시작
    searchNews();
}

/**
 * 뉴스 데이터를 검색하고 UI를 업데이트합니다. (페이지네이션 적용)
 */
async function searchNews() {
    const q = document.getElementById('newsSearch').value;
    const category = document.getElementById('newsCategory').value;
    const newsGrid = document.getElementById('newsGrid');
    
    // 로딩 표시 (선택 사항)
    newsGrid.innerHTML = '<p style="grid-column: 1/-1; text-align: center; color: #999;">로딩 중...</p>';

    try {
        const url = `/api/search?q=${encodeURIComponent(q)}&category=${encodeURIComponent(category)}&page=${currentPage}&limit=${currentLimit}`;
        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
        const data = await response.json();
        const news = data.news;
        
        newsGrid.innerHTML = ''; // 이전 내용 삭제
        
        if (!news || news.length === 0) {
            newsGrid.innerHTML = '<p style="grid-column: 1/-1; text-align: center; color: #999;">표시할 뉴스가 없습니다.</p>';
        } else {
            news.forEach(item => {
                const newsEl = createNewsElement(item);
                newsGrid.appendChild(newsEl);
            });
        }
        
        // 페이지네이션 컨트롤 업데이트
        updatePaginationControls(data.pagination);

    } catch (error) {
        console.error('뉴스 검색 오류:', error);
        newsGrid.innerHTML = '<p style="grid-column: 1/-1; text-align: center; color: red;">뉴스 검색 중 오류가 발생했습니다.</p>';
    }
}

/**
 * 모든 필터를 초기화하고 첫 페이지 뉴스를 로드합니다.
 */
function loadNews() {
    document.getElementById('newsSearch').value = '';
    document.getElementById('newsCategory').value = '';
    currentPage = 1;
    searchNews();
}

// ## Region: UI 렌더링 및 업데이트 ##

/**
 * 페이지네이션 컨트롤 UI를 업데이트합니다.
 * @param {object} pagination - 페이지네이션 정보 객체 { page, limit, total_pages, total_items }
 */
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
 * 뉴스 아이템 DOM 요소를 생성합니다.
 * @param {Object} item - 뉴스 아이템 데이터
 * @returns {HTMLElement} 생성된 뉴스 아이템 HTML 요소
 */
function createNewsElement(item) {
    const newsEl = document.createElement('div');
    newsEl.className = 'news-item';

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
    
    // --- Footer (actions) ---
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

/**
 * 위키 데이터를 로드하여 UI에 렌더링합니다.
 */
async function loadWiki() {
    const wikiGrid = document.getElementById('wikiGrid');
    if (!wikiGrid) return;
    try {
        const resp = await fetch('/api/wiki');
        if (!resp.ok) throw new Error(`HTTP error! status: ${resp.status}`);
        const wikis = await resp.json();
        renderWikiResults(wikis.results);
    } catch (e) {
        console.error('위키 로드 오류:', e);
        wikiGrid.innerHTML = '<p style="grid-column: 1/-1; text-align: center; color: red;">위키 로드 중 오류가 발생했습니다.</p>';
    }
}

/**
 * 크롤러를 실행합니다.
 */
async function runCrawler() {
    if (!confirm('크롤링을 실행하시겠습니까?')) return;
    try {
        const response = await fetch('/api/crawl', { method: 'POST' });
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();
        alert(`크롤링 완료: ${data.count}개의 뉴스가 추가되었습니다.`);
        loadNews(); // 크롤링 후 최신 데이터 로드
    } catch (error) {
        alert('크롤링 실패: ' + error.message);
    }
}

/**
 * 뉴스 기사를 삭제합니다.
 * @param {number|string} newsId - 삭제할 뉴스의 ID
 */
async function deleteNews(newsId) {
    if (!confirm('정말로 이 기사를 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.')) return;

    try {
        const response = await fetch(`/api/news/${newsId}`, { method: 'DELETE' });
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || '삭제에 실패했습니다.');
        }

        searchNews(); // 삭제 후 현재 페이지 다시 로드
    } catch (error) {
        console.error('기사 삭제 중 오류 발생:', error);
        alert(`오류: ${error.message}`);
    }
}

/**
 * 대시보드 데이터를 로드합니다.
 */
function loadDashboardData() {
    loadSourceStats();
    loadCategoryStats();
}

/**
 * 소스별 통계 데이터를 로드하여 UI에 렌더링합니다.
 */
async function loadSourceStats() {
    // ... 기존 함수 유지 ...
}

/**
 * 카테고리별 통계 데이터를 로드하여 UI에 렌더링합니다.
 */
async function loadCategoryStats() {
    // ... 기존 함수 유지 ...
}

/**
 * UI의 섹션을 전환합니다.
 * @param {string} section - 전환할 섹션의 ID
 */
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

/**
 * 카테고리별로 뉴스를 필터링합니다.
 * @param {string} category - 필터링할 카테고리
 */
function filterByCategory(category) {
    document.getElementById('newsCategory').value = category;
    document.getElementById('newsSearch').value = '';
    if (currentSection !== 'news') switchSection('news');
    currentPage = 1;
    searchNews();
}

/**
 * 통합 검색을 수행합니다.
 * @param {string} query - 검색어
 */
function searchContent(query) {
    if (currentSection === 'news') {
        document.getElementById('newsSearch').value = query;
        if(query.trim() === '') document.getElementById('newsCategory').value = '';
        currentPage = 1;
        searchNews();
    } else if (currentSection === 'wiki') {
        searchWiki(query);
    }
}

async function searchWiki(query) {
     const wikiGrid = document.getElementById('wikiGrid');
     if (!wikiGrid) return;
    try {
        const url = `/api/search?q=${encodeURIComponent(query)}`;
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
