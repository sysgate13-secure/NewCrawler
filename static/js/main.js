/**
 * @file main.js
 * @description 보안 뉴스 플랫폼의 프론트엔드 로직을 담당합니다.
 * @author Gemini
 * @date 2025-12-30
 */

// ## Region: 전역 변수 및 상수 ##
let currentSection = 'news';

const CATEGORY_LABELS = {
    'malware': '악성코드',
    'vulnerability': '취약점',
    'network': '네트워크',
    'web': '웹 보안',
    'crypto': '암호학',
    'trend': '기타'
};

const CATEGORY_EMOJI = {
    'malware': '🦠',
    'vulnerability': '🔓',
    'network': '🌐',
    'web': '💻',
    'crypto': '🔐',
    'trend': '📈'
};


// ## Region: 이벤트 리스너 ##

/**
 * 네비게이션 링크 클릭 시 섹션 전환 이벤트를 처리합니다.
 */
document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', function(e) {
        e.preventDefault();
        const section = this.dataset.section;
        switchSection(section);
        document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
        this.classList.add('active');
    });
});

/**
 * 페이지 로드 시 대시보드 데이터를 로드합니다.
 */
window.addEventListener('load', () => {
    if (currentSection === 'dashboard') {
        loadSourceStats();
        loadCategoryStats();
    }
});


// ## Region: UI 렌더링 함수 ##

/**
 * 위키 검색 결과를 UI에 렌더링합니다.
 * @param {Array<Object>} wikis - 렌더링할 위키 데이터 배열
 */
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
    const catLabel = CATEGORY_LABELS[item.category] || item.category || '';
    const catEmoji = CATEGORY_EMOJI[item.category] || '';
    
    const categorySpan = document.createElement('span');
    categorySpan.className = 'news-category';
    categorySpan.textContent = `${catEmoji} ${catLabel}`;

    const sourceSpan = document.createElement('span');
    sourceSpan.className = 'news-source';
    sourceSpan.textContent = item.source;

    metaDiv.appendChild(categorySpan);
    metaDiv.appendChild(sourceSpan);

    const dateSpan = document.createElement('span');
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
        summaryEl.textContent = item.summary;
        newsEl.appendChild(summaryEl);
    }

    return newsEl;
}


// ## Region: 데이터 로드 및 API 호출 함수 ##

/**
 * 뉴스 데이터를 검색하여 UI에 렌더링합니다.
 */
async function searchNews() {
    const q = document.getElementById('newsSearch').value;
    const category = document.getElementById('newsCategory').value;
    const newsGrid = document.getElementById('newsGrid');
    
    try {
        const url = `/api/search?q=${encodeURIComponent(q)}&category=${encodeURIComponent(category)}`;
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const results = await response.json();
        const news = results.news;
        
        newsGrid.innerHTML = '';
        
        if (news.length === 0) {
            newsGrid.innerHTML = '<p style="grid-column: 1/-1; text-align: center; color: #999;">검색 결과가 없습니다.</p>';
            return;
        }
        
        news.forEach(item => {
            const newsEl = createNewsElement(item);
            newsGrid.appendChild(newsEl);
        });
    } catch (error) {
        console.error('검색 오류:', error);
        newsGrid.innerHTML = '<p style="grid-column: 1/-1; text-align: center; color: red;">뉴스 검색 중 오류가 발생했습니다.</p>';
    }
}

/**
 * 최신 뉴스 데이터를 로드하여 UI에 렌더링합니다.
 */
async function loadNews() {
    const newsGrid = document.getElementById('newsGrid');
    try {
        const response = await fetch('/api/news');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const news = await response.json();
        
        document.getElementById('newsSearch').value = '';
        document.getElementById('newsCategory').value = '';
        
        newsGrid.innerHTML = '';
        
        news.forEach(item => {
            const newsEl = createNewsElement(item);
            newsGrid.appendChild(newsEl);
        });
    } catch (error) {
        console.error('뉴스 로드 오류:', error);
        newsGrid.innerHTML = '<p style="grid-column: 1/-1; text-align: center; color: red;">뉴스 로드 중 오류가 발생했습니다.</p>';
    }
}

/**
 * 위키 데이터를 로드하여 UI에 렌더링합니다.
 */
async function loadWiki() {
    const wikiGrid = document.getElementById('wikiGrid');
    try {
        const resp = await fetch('/api/wiki');
        if (!resp.ok) {
            throw new Error(`HTTP error! status: ${resp.status}`);
        }
        const wikis = await resp.json();
        renderWikiResults(wikis);
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
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        alert(`크롤링 완료: ${data.count}개의 뉴스가 추가되었습니다.`);
        location.reload();
    } catch (error) {
        alert('크롤링 실패: ' + error.message);
    }
}

/**
 * 소스별 통계 데이터를 로드하여 UI에 렌더링합니다.
 */
async function loadSourceStats() {
    const statsEl = document.getElementById('source-stats');
    try {
        const response = await fetch('/api/stats/sources');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const stats = await response.json();
        
        if (!stats || stats.length === 0) {
            statsEl.innerHTML = '<p style="text-align: center; color: #999;">통계 데이터가 없습니다.</p>';
            return;
        }

        statsEl.innerHTML = '';
        stats.forEach(stat => {
            const el = document.createElement('div');
            el.className = 'source-stat-item';
            el.innerHTML = `
                <span class="source-name">${stat.source}</span>
                <span class="source-count">${stat.count}</span>
            `;
            statsEl.appendChild(el);
        });
    } catch (error) {
        console.error('소스 통계 로드 오류:', error);
        statsEl.innerHTML = '<p style="text-align: center; color: red;">소스 통계 로드 중 오류가 발생했습니다.</p>';
    }
}

/**
 * 카테고리별 통계 데이터를 로드하여 UI에 렌더링합니다.
 */
async function loadCategoryStats() {
    const statsEl = document.getElementById('category-stats');
    try {
        const response = await fetch('/api/stats/categories');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const stats = await response.json();
        
        if (!stats || stats.length === 0) {
            statsEl.innerHTML = '<p style="text-align: center; color: #999;">통계 데이터가 없습니다.</p>';
            return;
        }

        statsEl.innerHTML = '';
        stats.forEach(stat => {
            const el = document.createElement('div');
            el.className = 'source-stat-item';
            el.innerHTML = `
                <span class="source-name">${stat.label}</span>
                <span class="source-count">${stat.count}</span>
            `;
            statsEl.appendChild(el);
        });
    } catch (error) {
        console.error('카테고리 통계 로드 오류:', error);
        statsEl.innerHTML = '<p style="text-align: center; color: red;">카테고리 통계 로드 중 오류가 발생했습니다.</p>';
    }
}


// ## Region: 유틸리티 함수 ##

/**
 * UI의 섹션을 전환합니다.
 * @param {string} section - 전환할 섹션의 ID
 */
function switchSection(section) {
    document.getElementById('news-section').style.display = 'none';
    document.getElementById('wiki-section').style.display = 'none';
    document.getElementById('dashboard-section').style.display = 'none';
    document.getElementById(section + '-section').style.display = 'block';
    currentSection = section;
    
    if (section === 'dashboard') {
        loadSourceStats();
        loadCategoryStats();
    }
}

/**
 * 카테고리별로 뉴스를 필터링합니다.
 * @param {string} category - 필터링할 카테고리
 */
function filterByCategory(category) {
    // 사이드바 카테고리는 뉴스 필터에만 적용 (지식사전은 별도 관리)
    document.getElementById('newsCategory').value = category;
    document.getElementById('newsSearch').value = '';
    // 자동으로 뉴스 섹션 표시
    if (currentSection !== 'news') switchSection('news');
    searchNews();
}

/**
 * 통합 검색을 수행합니다.
 * @param {string} query - 검색어
 */
async function searchContent(query) {
    // 상단 통합 검색: 현재 선택된 섹션을 기준으로 API 호출
    if (!query || query.trim().length === 0) {
        // 빈 쿼리는 각 섹션의 기본 로드로 리셋
        if (currentSection === 'news') loadNews();
        if (currentSection === 'wiki') loadWiki();
        return;
    }

    if (currentSection === 'news') {
        document.getElementById('newsSearch').value = query;
        document.getElementById('newsCategory').value = '';
        searchNews();
        return;
    }

    if (currentSection === 'wiki') {
        // wiki API로 검색
        try {
            const url = `/api/wiki/search?q=${encodeURIComponent(query)}`;
            const resp = await fetch(url);
            const wikis = await resp.json();
            renderWikiResults(wikis);
        } catch (e) {
            console.error('위키 검색 오류:', e);
        }
        return;
    }

    // 기본: 뉴스+위키 모두 검색 후 간단히 콘솔에 표시
    try {
        const newsResp = await fetch(`/api/news/search?q=${encodeURIComponent(query)}`);
        const news = await newsResp.json();
        const wikiResp = await fetch(`/api/wiki/search?q=${encodeURIComponent(query)}`);
        const w = await wikiResp.json();
        console.log('통합 검색 결과 - news:', news.length, 'wiki:', w.length);
    } catch (e) {
        console.error('통합 검색 오류:', e);
    }
}
