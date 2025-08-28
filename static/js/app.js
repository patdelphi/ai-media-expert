// 全局变量
let currentPage = 'dashboard';
let currentVideoPage = 1;
let videosPerPage = 24;
let totalVideos = 0;
let videos = [];

// API基础URL
const API_BASE = '/api/v1';

// 页面初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    setupNavigation();
    setupEventListeners();
    loadDashboardData();
    showPage('dashboard');
}

// 导航设置
function setupNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const pageId = this.dataset.page;
            showPage(pageId);
            updateActiveNavLink(this);
        });
    });
}

function showPage(pageId) {
    // 隐藏所有页面
    const pages = document.querySelectorAll('.page');
    pages.forEach(page => page.classList.remove('active'));
    
    // 显示目标页面
    const targetPage = document.getElementById(`${pageId}-page`);
    if (targetPage) {
        targetPage.classList.add('active');
        currentPage = pageId;
        
        // 根据页面加载相应数据
        switch(pageId) {
            case 'dashboard':
                loadDashboardData();
                break;
            case 'library':
                loadVideoLibrary();
                break;
            case 'analysis':
                loadAnalysisVideos();
                break;
        }
    }
}

function updateActiveNavLink(activeLink) {
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => link.classList.remove('active'));
    activeLink.classList.add('active');
}

// 事件监听器设置
function setupEventListeners() {
    // 文件上传
    const fileInput = document.getElementById('file-input');
    const uploadArea = document.getElementById('upload-area');
    const uploadForm = document.getElementById('upload-form');
    
    if (fileInput && uploadArea && uploadForm) {
        // 拖拽上传
        uploadArea.addEventListener('dragover', handleDragOver);
        uploadArea.addEventListener('dragleave', handleDragLeave);
        uploadArea.addEventListener('drop', handleDrop);
        
        // 文件选择
        fileInput.addEventListener('change', handleFileSelect);
        
        // 表单提交
        uploadForm.addEventListener('submit', handleUploadSubmit);
    }
    
    // 搜索
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(handleSearch, 300));
    }
    
    // 筛选
    const platformFilter = document.getElementById('platform-filter');
    const statusFilter = document.getElementById('status-filter');
    if (platformFilter) platformFilter.addEventListener('change', handleFilter);
    if (statusFilter) statusFilter.addEventListener('change', handleFilter);
    
    // 分页
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    const pageSize = document.getElementById('page-size');
    
    if (prevBtn) prevBtn.addEventListener('click', () => changePage(currentVideoPage - 1));
    if (nextBtn) nextBtn.addEventListener('click', () => changePage(currentVideoPage + 1));
    if (pageSize) pageSize.addEventListener('change', handlePageSizeChange);
    
    // 分析
    const startAnalysisBtn = document.getElementById('start-analysis');
    if (startAnalysisBtn) {
        startAnalysisBtn.addEventListener('click', handleStartAnalysis);
    }
}

// API请求函数
async function apiRequest(endpoint, options = {}) {
    try {
        showLoading();
        const response = await fetch(`${API_BASE}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('API request failed:', error);
        showNotification('请求失败: ' + error.message, 'error');
        throw error;
    } finally {
        hideLoading();
    }
}

// 仪表板数据加载
async function loadDashboardData() {
    try {
        // 这里应该调用实际的API端点
        // 暂时使用模拟数据
        const stats = {
            totalVideos: 0,
            totalDownloads: 0,
            totalAnalysis: 0,
            completedTasks: 0
        };
        
        // 尝试获取真实数据
        try {
            const videosResponse = await fetch('/api/v1/videos?limit=1');
            if (videosResponse.ok) {
                const videosData = await videosResponse.json();
                stats.totalVideos = videosData.total || 0;
            }
        } catch (e) {
            console.log('Videos API not available, using mock data');
        }
        
        updateDashboardStats(stats);
    } catch (error) {
        console.error('Failed to load dashboard data:', error);
    }
}

function updateDashboardStats(stats) {
    document.getElementById('total-videos').textContent = stats.totalVideos;
    document.getElementById('total-downloads').textContent = stats.totalDownloads;
    document.getElementById('total-analysis').textContent = stats.totalAnalysis;
    document.getElementById('completed-tasks').textContent = stats.completedTasks;
}

// 文件上传处理
function handleDragOver(e) {
    e.preventDefault();
    e.currentTarget.classList.add('dragover');
}

function handleDragLeave(e) {
    e.preventDefault();
    e.currentTarget.classList.remove('dragover');
}

function handleDrop(e) {
    e.preventDefault();
    e.currentTarget.classList.remove('dragover');
    
    const files = e.dataTransfer.files;
    handleFiles(files);
}

function handleFileSelect(e) {
    const files = e.target.files;
    handleFiles(files);
}

function handleFiles(files) {
    const fileArray = Array.from(files);
    const videoFiles = fileArray.filter(file => file.type.startsWith('video/'));
    
    if (videoFiles.length === 0) {
        showNotification('请选择视频文件', 'warning');
        return;
    }
    
    if (videoFiles.length > 10) {
        showNotification('一次最多上传10个文件', 'warning');
        return;
    }
    
    // 显示选中的文件
    const fileNames = videoFiles.map(file => file.name).join(', ');
    showNotification(`已选择 ${videoFiles.length} 个文件: ${fileNames}`, 'success');
}

async function handleUploadSubmit(e) {
    e.preventDefault();
    
    const fileInput = document.getElementById('file-input');
    const title = document.getElementById('video-title').value;
    const description = document.getElementById('video-description').value;
    const autoAnalyze = document.getElementById('auto-analyze').checked;
    
    if (!fileInput.files.length) {
        showNotification('请选择要上传的文件', 'warning');
        return;
    }
    
    const formData = new FormData();
    
    // 添加文件
    Array.from(fileInput.files).forEach(file => {
        formData.append('files', file);
    });
    
    // 添加其他数据
    if (title) formData.append('title', title);
    if (description) formData.append('description', description);
    formData.append('auto_analyze', autoAnalyze);
    
    try {
        showUploadProgress();
        
        const response = await fetch('/api/v1/upload/batch', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`上传失败: ${response.status}`);
        }
        
        const result = await response.json();
        hideUploadProgress();
        
        showNotification(`成功上传 ${result.length} 个文件`, 'success');
        
        // 清空表单
        document.getElementById('upload-form').reset();
        
        // 刷新视频库
        if (currentPage === 'library') {
            loadVideoLibrary();
        }
        
    } catch (error) {
        hideUploadProgress();
        showNotification('上传失败: ' + error.message, 'error');
    }
}

function showUploadProgress() {
    document.getElementById('upload-progress').style.display = 'block';
    // 模拟进度
    let progress = 0;
    const interval = setInterval(() => {
        progress += Math.random() * 10;
        if (progress >= 100) {
            progress = 100;
            clearInterval(interval);
        }
        updateUploadProgress(progress);
    }, 200);
}

function hideUploadProgress() {
    document.getElementById('upload-progress').style.display = 'none';
    updateUploadProgress(0);
}

function updateUploadProgress(progress) {
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    
    if (progressFill) progressFill.style.width = `${progress}%`;
    if (progressText) progressText.textContent = `${Math.round(progress)}%`;
}

// 视频库加载
async function loadVideoLibrary() {
    try {
        const searchQuery = document.getElementById('search-input')?.value || '';
        const platformFilter = document.getElementById('platform-filter')?.value || '';
        const statusFilter = document.getElementById('status-filter')?.value || '';
        
        const params = new URLSearchParams({
            page: currentVideoPage,
            limit: videosPerPage
        });
        
        if (searchQuery) params.append('search', searchQuery);
        if (platformFilter) params.append('platform', platformFilter);
        if (statusFilter) params.append('status', statusFilter);
        
        try {
            const response = await fetch(`/api/v1/videos?${params}`);
            if (response.ok) {
                const data = await response.json();
                videos = data.items || [];
                totalVideos = data.total || 0;
            } else {
                // 使用模拟数据
                videos = generateMockVideos();
                totalVideos = videos.length;
            }
        } catch (e) {
            // API不可用时使用模拟数据
            videos = generateMockVideos();
            totalVideos = videos.length;
        }
        
        renderVideoGrid();
        updatePagination();
        
    } catch (error) {
        console.error('Failed to load video library:', error);
        showNotification('加载视频库失败', 'error');
    }
}

function generateMockVideos() {
    return [
        {
            id: 1,
            title: '示例视频 1',
            platform: 'local',
            status: 'uploaded',
            created_at: new Date().toISOString(),
            file_size: 1024000
        },
        {
            id: 2,
            title: '示例视频 2',
            platform: 'local',
            status: 'analyzed',
            created_at: new Date().toISOString(),
            file_size: 2048000
        }
    ];
}

function renderVideoGrid() {
    const videoGrid = document.getElementById('video-grid');
    if (!videoGrid) return;
    
    if (videos.length === 0) {
        videoGrid.innerHTML = `
            <div class="no-videos">
                <i class="fas fa-video" style="font-size: 3rem; color: #ccc; margin-bottom: 1rem;"></i>
                <p style="color: #666;">暂无视频，请先上传视频文件</p>
            </div>
        `;
        return;
    }
    
    videoGrid.innerHTML = videos.map(video => createVideoCard(video)).join('');
}

function createVideoCard(video) {
    const formatFileSize = (bytes) => {
        if (!bytes) return 'Unknown';
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
    };
    
    const formatDate = (dateString) => {
        if (!dateString) return 'Unknown';
        return new Date(dateString).toLocaleDateString('zh-CN');
    };
    
    const getStatusBadge = (status) => {
        const badges = {
            'uploaded': '<span class="badge badge-primary">已上传</span>',
            'analyzed': '<span class="badge badge-success">已分析</span>',
            'processing': '<span class="badge badge-warning">处理中</span>',
            'failed': '<span class="badge badge-danger">失败</span>'
        };
        return badges[status] || '<span class="badge badge-secondary">未知</span>';
    };
    
    return `
        <div class="video-card">
            <div class="video-thumbnail">
                <i class="fas fa-play"></i>
            </div>
            <div class="video-info">
                <h4>${video.title || '未命名视频'}</h4>
                <div class="video-meta">
                    <p><i class="fas fa-calendar"></i> ${formatDate(video.created_at)}</p>
                    <p><i class="fas fa-hdd"></i> ${formatFileSize(video.file_size)}</p>
                    <p><i class="fas fa-globe"></i> ${video.platform || 'local'}</p>
                </div>
                <div class="video-status">
                    ${getStatusBadge(video.status)}
                </div>
                <div class="video-actions">
                    <button class="btn btn-primary btn-sm" onclick="playVideo(${video.id})">
                        <i class="fas fa-play"></i>
                    </button>
                    <button class="btn btn-success btn-sm" onclick="analyzeVideo(${video.id})">
                        <i class="fas fa-brain"></i>
                    </button>
                    <button class="btn btn-outline btn-sm" onclick="deleteVideo(${video.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        </div>
    `;
}

// 分页处理
function updatePagination() {
    const totalPages = Math.ceil(totalVideos / videosPerPage);
    const pageInfo = document.getElementById('page-info');
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    
    if (pageInfo) {
        pageInfo.textContent = `第 ${currentVideoPage} 页，共 ${totalPages} 页`;
    }
    
    if (prevBtn) {
        prevBtn.disabled = currentVideoPage <= 1;
    }
    
    if (nextBtn) {
        nextBtn.disabled = currentVideoPage >= totalPages;
    }
}

function changePage(page) {
    const totalPages = Math.ceil(totalVideos / videosPerPage);
    if (page < 1 || page > totalPages) return;
    
    currentVideoPage = page;
    loadVideoLibrary();
}

function handlePageSizeChange(e) {
    videosPerPage = parseInt(e.target.value);
    currentVideoPage = 1;
    loadVideoLibrary();
}

// 搜索和筛选
function handleSearch(e) {
    currentVideoPage = 1;
    loadVideoLibrary();
}

function handleFilter() {
    currentVideoPage = 1;
    loadVideoLibrary();
}

// 分析功能
async function loadAnalysisVideos() {
    try {
        const select = document.getElementById('analysis-video');
        if (!select) return;
        
        // 清空选项
        select.innerHTML = '<option value="">请选择要分析的视频</option>';
        
        // 加载视频列表
        try {
            const response = await fetch('/api/v1/videos?limit=100');
            if (response.ok) {
                const data = await response.json();
                const videos = data.items || [];
                
                videos.forEach(video => {
                    const option = document.createElement('option');
                    option.value = video.id;
                    option.textContent = video.title || `视频 ${video.id}`;
                    select.appendChild(option);
                });
            }
        } catch (e) {
            console.log('Videos API not available for analysis');
        }
        
    } catch (error) {
        console.error('Failed to load analysis videos:', error);
    }
}

async function handleStartAnalysis() {
    const videoId = document.getElementById('analysis-video').value;
    const analysisType = document.querySelector('input[name="analysis-type"]:checked').value;
    
    if (!videoId) {
        showNotification('请选择要分析的视频', 'warning');
        return;
    }
    
    try {
        const response = await apiRequest('/analysis/tasks', {
            method: 'POST',
            body: JSON.stringify({
                video_id: parseInt(videoId),
                analysis_type: analysisType
            })
        });
        
        showNotification('分析任务已创建', 'success');
        
        // 显示分析结果区域
        const resultsDiv = document.getElementById('analysis-results');
        const resultsContent = document.getElementById('results-content');
        
        if (resultsDiv && resultsContent) {
            resultsDiv.style.display = 'block';
            resultsContent.innerHTML = `
                <div class="analysis-progress">
                    <p>分析进行中...</p>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: 0%"></div>
                    </div>
                </div>
            `;
        }
        
    } catch (error) {
        showNotification('创建分析任务失败', 'error');
    }
}

// 视频操作
function playVideo(videoId) {
    showNotification('播放功能开发中', 'info');
}

function analyzeVideo(videoId) {
    // 切换到分析页面并选择视频
    showPage('analysis');
    updateActiveNavLink(document.querySelector('[data-page="analysis"]'));
    
    setTimeout(() => {
        const select = document.getElementById('analysis-video');
        if (select) {
            select.value = videoId;
        }
    }, 100);
}

async function deleteVideo(videoId) {
    if (!confirm('确定要删除这个视频吗？')) {
        return;
    }
    
    try {
        await apiRequest(`/videos/${videoId}`, {
            method: 'DELETE'
        });
        
        showNotification('视频已删除', 'success');
        loadVideoLibrary();
        
    } catch (error) {
        showNotification('删除失败', 'error');
    }
}

// 工具函数
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function showLoading() {
    const loading = document.getElementById('loading');
    if (loading) loading.style.display = 'flex';
}

function hideLoading() {
    const loading = document.getElementById('loading');
    if (loading) loading.style.display = 'none';
}

function showNotification(message, type = 'info', duration = 3000) {
    const notifications = document.getElementById('notifications');
    if (!notifications) return;
    
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span>${message}</span>
            <button onclick="this.parentElement.parentElement.remove()" style="background: none; border: none; font-size: 1.2rem; cursor: pointer;">&times;</button>
        </div>
    `;
    
    notifications.appendChild(notification);
    
    // 自动移除
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, duration);
}

// 添加样式到页面
const additionalStyles = `
.badge {
    display: inline-block;
    padding: 0.25rem 0.5rem;
    font-size: 0.75rem;
    font-weight: 600;
    border-radius: 0.25rem;
    text-transform: uppercase;
}

.badge-primary { background: #667eea; color: white; }
.badge-success { background: #28a745; color: white; }
.badge-warning { background: #ffc107; color: #333; }
.badge-danger { background: #dc3545; color: white; }
.badge-secondary { background: #6c757d; color: white; }

.no-videos {
    grid-column: 1 / -1;
    text-align: center;
    padding: 3rem;
}

.analysis-progress {
    text-align: center;
    padding: 2rem;
}
`;

const styleSheet = document.createElement('style');
styleSheet.textContent = additionalStyles;
document.head.appendChild(styleSheet);