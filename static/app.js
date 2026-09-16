// Asmary Tender Monitor Frontend Logic
let allTenders = [];
let currentCategoryFilter = 'all';

document.addEventListener('DOMContentLoaded', () => {
    loadCachedTenders();
    checkScanStatus();
    setInterval(checkScanStatus, 2500);

    // Search filter listener
    document.getElementById('searchInput').addEventListener('input', applyFilters);

    // Pill category listeners
    document.querySelectorAll('.filter-pills .pill').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.filter-pills .pill').forEach(p => p.classList.remove('active'));
            btn.classList.add('active');
            currentCategoryFilter = btn.getAttribute('data-filter');
            applyFilters();
        });
    });
});

async function loadCachedTenders() {
    try {
        const res = await fetch('/api/tenders');
        const data = await res.json();
        
        allTenders = data.tenders || [];
        document.getElementById('matchedCount').textContent = allTenders.length;
        document.getElementById('totalScanned').textContent = data.total_scanned_notices || (allTenders.length * 20) || 0;
        document.getElementById('lastUpdated').textContent = data.last_updated || 'هنوز ثبت نشده';
        
        applyFilters();
    } catch (e) {
        console.error('Error loading tenders:', e);
    }
}

function applyFilters() {
    const searchVal = document.getElementById('searchInput').value.trim().toLowerCase();
    
    const filtered = allTenders.filter(t => {
        const titleMatch = t.title.toLowerCase().includes(searchVal);
        const clientMatch = (t.client || '').toLowerCase().includes(searchVal);
        const textMatch = (t.full_text || '').toLowerCase().includes(searchVal);
        const idMatch = (t.tender_id || '').toLowerCase().includes(searchVal);

        const matchesSearch = !searchVal || titleMatch || clientMatch || textMatch || idMatch;

        let matchesCat = true;
        if (currentCategoryFilter !== 'all') {
            const services = t.matched_services || [];
            matchesCat = services.includes(currentCategoryFilter);
        }

        return matchesSearch && matchesCat;
    });

    renderTable(filtered);
    document.getElementById('filteredCountBadge').textContent = `${filtered.length} مورد`;
}

function renderTable(tenders) {
    const tbody = document.getElementById('tenderTableBody');
    if (!tenders || tenders.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center text-muted py-5">
                    هیچ مناقصه منطبقی یافت نشد. دکمه «شروع پایش ۵۰ صفحه» را کلیک کنید.
                </td>
            </tr>
        `;
        return;
    }

    let rowsHtml = '';
    tenders.forEach((t, i) => {
        const services = t.matched_services || [];
        const badges = services.map(s => `<span class="service-badge">${s}</span>`).join(' ');

        rowsHtml += `
            <tr>
                <td class="text-center font-bold text-muted">${i + 1}</td>
                <td style="font-weight: 600; max-width: 400px;">${t.title}</td>
                <td><span class="client-tag">${t.client}</span></td>
                <td>${badges}</td>
                <td class="text-center" style="font-family: monospace;">${t.tender_id || '—'}</td>
                <td class="text-center">${t.date || '—'}</td>
                <td class="text-center">
                    <a href="${t.link}" target="_blank" class="view-btn">اسناد شانا ↗</a>
                </td>
            </tr>
        `;
    });

    tbody.innerHTML = rowsHtml;
}

async function startScan(pages = 50) {
    const btn = document.getElementById('scanBtn');
    btn.disabled = true;
    document.getElementById('btnText').textContent = 'در حال ارسال درخواست...';

    try {
        const res = await fetch('/api/scan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ pages: pages })
        });
        const data = await res.json();
        if (data.success) {
            document.getElementById('progressCard').classList.remove('hidden');
        } else {
            alert(data.message || 'خطا در اجرای اسکن');
            btn.disabled = false;
            document.getElementById('btnText').textContent = 'شروع پایش ۵۰ صفحه اخیر شانا';
        }
    } catch (e) {
        alert('خطای ارتباط با سرور: ' + e);
        btn.disabled = false;
        document.getElementById('btnText').textContent = 'شروع پایش ۵۰ صفحه اخیر شانا';
    }
}

async function checkScanStatus() {
    try {
        const res = await fetch('/api/status');
        const status = await res.json();
        
        const card = document.getElementById('progressCard');
        const btn = document.getElementById('scanBtn');
        const btnText = document.getElementById('btnText');
        const pBar = document.getElementById('progressBar');
        const pCounter = document.getElementById('pageCounter');

        if (status.is_scanning) {
            card.classList.remove('hidden');
            btn.disabled = true;
            btnText.textContent = `در حال اسکن (صفحه ${status.current_page} از ${status.total_pages})...`;
            
            const pct = Math.round((status.current_page / status.total_pages) * 100);
            pBar.style.width = `${pct}%`;
            pCounter.textContent = `صفحه ${status.current_page} از ${status.total_pages} (${pct}%)`;
        } else {
            if (!card.classList.contains('hidden') && btn.disabled) {
                // Just completed
                card.classList.add('hidden');
                btn.disabled = false;
                btnText.textContent = 'شروع پایش ۵۰ صفحه اخیر شانا';
                loadCachedTenders();
            }
        }
    } catch (e) {
        // quiet error on polling
    }
}
