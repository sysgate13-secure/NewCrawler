/**
 * @file main.js
 * @description 보안 뉴스 플랫폼의 프론트엔드 로직을 담당합니다.
 * @author Gemini
 * @date 2026-01-01
 */

// ## Region: 전역 변수 및 상수 ##
let currentSection = 'news';
var currentPage = window.currentPage || 1;
var currentLimit = window.currentLimit || 20;
var totalPages = window.totalPages || 1;

const CATEGORY_LABELS = {
    'malware': '악성코드', 'vulnerability': '취약점', 'network': '네트워크',
    'web': '웹 보안', 'crypto': '암호학', 'trend': '기타'
};

// ## Region: 이벤트 리스너 ##
document.addEventListener('DOMContentLoaded', () => {
    initializePage();

    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const section = this.dataset.section;
            if (section) {
                switchSection(section);
                document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
                this.classList.add('active');
            }
        });
    });

    const navToggle = document.getElementById('nav-toggle');
    const navMenu = document.getElementById('nav-menu');

    navToggle.addEventListener('click', () => {
        navMenu.classList.toggle('active');
        navToggle.classList.toggle('active');
    });

    if (currentSection === 'dashboard') {
        loadDashboardData();
    }
});

function initializePage() {
    initializePagination();
    // 초기 섹션 활성화
    switchSection(currentSection);
    // 브라우저 알림 권한 요청
    if ("Notification" in window && Notification.permission === "default") {
        Notification.requestPermission();
    }
}


// ## Region: 페이지네이션 및 데이터 로드 ##

function initializePagination() {
    const pageSizeEl = document.getElementById('pageSize');
    
    if (pageSizeEl) {
        currentLimit = parseInt(pageSizeEl.value, 10) || 20;
    }
    
    // 서버에서 전달된 초기 페이지네이션 정보 사용
    const paginationNav = document.getElementById('pagination-nav');
    if (paginationNav) {
        // renderPagination이 index.html 내부 스크립트에서 이미 실행됨
        // 초기 totalPages와 currentPage는 이미 설정됨
    }
}

function changePage(direction) {
    let newPage;
    if (direction === 'prev') {
        newPage = currentPage - 1;
    } else if (direction === 'next') {
        newPage = currentPage + 1;
    } else {
        newPage = direction;
    }

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

async function fetchNews() {
    const q = document.getElementById('newsSearch').value;
    const category = document.getElementById('newsCategory').value;
    const newsGrid = document.getElementById('newsGrid');
    
    newsGrid.innerHTML = '<p class="loading-message">로딩 중...</p>';

    try {
        const url = `/api/search?q=${encodeURIComponent(q)}&category=${encodeURIComponent(category)}&page=${currentPage}&limit=${currentLimit}&index=news`;
        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
        const data = await response.json();
        renderNews(data.news);
        
        totalPages = data.pagination.total_pages;
        
        // totalItems 업데이트
        const totalItemsEl = document.getElementById('totalItems');
        if (totalItemsEl) {
            totalItemsEl.textContent = `총 ${data.pagination.total_items}개`;
        }
        
        renderPagination(totalPages, currentPage);

    } catch (error) {
        console.error('뉴스 검색 오류:', error);
        newsGrid.innerHTML = '<p class="error-message">뉴스 검색 중 오류가 발생했습니다.</p>';
    }
}

function filterNews() {
    const q = document.getElementById('newsSearch').value.toLowerCase();
    const newsItems = document.querySelectorAll('#newsGrid .news-item');

    newsItems.forEach(item => {
        const title = (item.querySelector('.news-title a')?.textContent || '').toLowerCase();
        const summary = (item.querySelector('.news-summary')?.textContent || '').toLowerCase();
        
        if (title.includes(q) || summary.includes(q)) {
            item.classList.remove('hidden');
        } else {
            item.classList.add('hidden');
        }
    });
}

function loadNews() {
    document.getElementById('newsSearch').value = '';
    document.getElementById('newsCategory').value = '';
    currentPage = 1;
    fetchNews();
}

// ## Region: UI 렌더링 및 업데이트 ##

function renderNews(news) {
    const newsGrid = document.getElementById('newsGrid');
    newsGrid.innerHTML = '';

    if (!news || news.length === 0) {
        newsGrid.innerHTML = '<p class="info-message">표시할 뉴스가 없습니다.</p>';
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
    newsEl.dataset.category = item.category || '';

    const sourceBadgeClass = item.source && item.source.includes('보안뉴스') 
        ? 'badge-source-kr' 
        : 'badge-source-en';
    const sourceIcon = item.source && item.source.includes('보안뉴스') ? '🇰🇷' : '🌍';

    let sourceLink;
    if (item.source && item.source.includes('보안뉴스')) {
        sourceLink = '<a href="https://www.boannews.com" target="_blank">www.boannews.com</a>';
    } else if (item.source && item.source.includes('HackRead')) {
        sourceLink = '<a href="https://www.hackread.com" target="_blank">www.hackread.com</a>';
    } else {
        sourceLink = `<span>${item.source || ''}</span>`;
    }

    newsEl.innerHTML = `
        <div class="news-meta">
            <div class="news-meta-start">
                <span class="badge badge-category">${CATEGORY_LABELS[item.category] || item.category || ''}</span>
                <span class="badge ${sourceBadgeClass}">${sourceIcon} ${item.source}</span>
            </div>
            <span>${item.date}</span>
        </div>
        <h3 class="news-title">
            <a href="${item.url}" target="_blank">${item.title}</a>
        </h3>
        ${item.summary ? `<p class="news-summary">${item.summary.replace(/<br\s*\/?>/gi, ' ')}</p>` : ''}
        <div class="news-footer">
            <div>📰 출처: ${sourceLink}</div>
            <button class="btn btn-danger" onclick="deleteNews('${item.id}')">삭제</button>
        </div>
    `;
    return newsEl;
}

function renderPagination(totalPages, currentPage) {
    const paginationNav = document.getElementById('pagination-nav');
    if (!paginationNav) return;
    
    let paginationHtml = '<ul class="pagination">';

    // Previous button
    paginationHtml += `<li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
        <a class="page-link" href="#" onclick="event.preventDefault(); changePage('prev')">이전</a>
    </li>`;

    // Page numbers
    for (let i = 1; i <= totalPages; i++) {
        paginationHtml += `<li class="page-item ${i === currentPage ? 'active' : ''}">
            <a class="page-link" href="#" onclick="event.preventDefault(); changePage(${i})">${i}</a>
        </li>`;
    }

    // Next button
    paginationHtml += `<li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
        <a class="page-link" href="#" onclick="event.preventDefault(); changePage('next')">다음</a>
    </li>`;

    paginationHtml += '</ul>';
    paginationNav.innerHTML = paginationHtml;
}

// ## Region: 기타 API 호출 및 유틸리티 ##

async function runCrawler() {
    const crawlBtn = document.querySelector('.crawl-btn');
    if (!confirm('최신 뉴스를 수집하기 위해 크롤링을 실행하시겠습니까?')) return;

    // 버튼 상태 변경 (시각적 피드백 및 중복 클릭 방지)
    const originalContent = crawlBtn.innerHTML;
    crawlBtn.disabled = true;
    crawlBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> ⏳ 크롤링 중...';

    try {
        const response = await fetch('/api/crawl', { method: 'POST' });
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();
        
        const message = `✅ 크롤링 완료: ${data.count}개의 새로운 뉴스가 추가되었습니다.`;
        
        // 1. 브라우저 데스크톱 알림
        if ("Notification" in window && Notification.permission === "granted") {
            new Notification("보안 뉴스 플랫폼", {
                body: message,
                icon: "/static/favicon.ico"
            });
        }
        
        // 2. 브라우저 알림창
        alert(message);
        loadNews();
    } catch (error) {
        alert('❌ 크롤링 실패: ' + error.message);
    } finally {
        // 버튼 상태 복구
        crawlBtn.disabled = false;
        crawlBtn.innerHTML = originalContent;
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
        fetchNews();
    } catch (error) {
        console.error('기사 삭제 중 오류 발생:', error);
        alert(`오류: ${error.message}`);
    }
}

function switchSection(section) {
    document.querySelectorAll('.news-content, .wiki-content, .dashboard-content').forEach(el => {
        el.classList.remove('active');
    });
    const sectionEl = document.getElementById(section + '-section');
    if (sectionEl) {
        sectionEl.classList.add('active');
    }
    currentSection = section;
    
    if (section === 'dashboard') {
        loadDashboardData();
    }
}

function filterByCategory(category) {
    switchSection('news');
    document.getElementById('newsCategory').value = category;
    document.getElementById('newsSearch').value = '';
    currentPage = 1;
    fetchNews();
}

function searchContent(query) {
    if (currentSection === 'news') {
        document.getElementById('newsSearch').value = query;
        filterNews();
    } else if (currentSection === 'wiki') {
        searchWiki(query);
    }
}

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
        wikiGrid.innerHTML = '<p class="error-message">검색 중 오류가 발생했습니다.</p>';
    }
}

function renderWikiResults(wikis) {
    const wikiGrid = document.getElementById('wikiGrid');
    if (!wikiGrid) return;
    wikiGrid.innerHTML = '';
    if (!wikis || wikis.length === 0) {
        wikiGrid.innerHTML = '<p class="info-message">검색 결과가 없습니다.</p>';
        return;
    }
    wikis.forEach(item => {
        const el = document.createElement('div');
        el.className = 'wiki-card';
        el.onclick = () => location.href = `/wiki/${item.id}`;

        const tagsHtml = (item.tags || '').split(',').filter(t => t).map(t => `<span class="tag">#${t}</span>`).join('');
        
        let badgeHtml = '';
        if (item.type === 'auto') {
            badgeHtml = '<span class="badge badge-wiki-auto">🤖 자동수집</span>';
        } else if (item.type === 'manual') {
            badgeHtml = '<span class="badge badge-wiki-manual">✍️ 수동작성</span>';
        } else {
            badgeHtml = '<span class="badge badge-wiki-expert">📚 전문문서</span>';
        }

        el.innerHTML = `
            <div class="wiki-header">
                <div class="badge badge-category">${item.category || ''}</div>
                ${badgeHtml}
            </div>
            <h3 class="wiki-title">${item.title}</h3>
            ${item.preview ? `<p class="wiki-preview">${item.preview}</p>` : ''}
            ${tagsHtml ? `<div class="wiki-tags">${tagsHtml}</div>` : ''}
        `;
        
        wikiGrid.appendChild(el);
    });
}

function loadDashboardData() {
    // This function can be implemented to load and render dashboard statistics
}
