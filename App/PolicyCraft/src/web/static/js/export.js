// Funkcja do eksportu analiz do pliku CSV
function exportAnalysesTable(analysesData) {
    try {
        // Przygotuj dane do eksportu
        const exportData = analysesData.map(analysis => ({
            'University': analysis.university,
            'Classification': analysis.classification,
            'Confidence': analysis.confidence,
            'Upload Date': formatDateForExport(analysis.upload_date || ''),
            'Analysis Date': formatDateForExport(analysis.analysis_date || ''),
            'Top Themes': analysis.top_themes.replace(/\s+/g, ' ').trim(),
            'Is Baseline': analysis.is_baseline,
            'File Name': analysis.filename,
            'Analysis ID': analysis.analysis_id
        }));

        // Konwersja do CSV z użyciem PapaParse
        const csv = Papa.unparse(exportData, {
            quotes: true,
            header: true,
            delimiter: ',',
            newline: '\r\n',
            skipEmptyLines: true
        });

        // Utwórz plik do pobrania
        const blob = new Blob(["\uFEFF" + csv], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.setAttribute('href', url);
        link.setAttribute('download', `policy_analyses_${new Date().toISOString().split('T')[0]}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);

    } catch (error) {
        console.error('Error while exporting data:', error);
        alert('An error occurred during data export. Check the browser console for more information.');
    }
}

// Helper function to format date
function formatDateForExport(dateString) {
    if (!dateString) return '';
    try {
        const date = new Date(dateString);
        return date.toISOString(); // Returns date in ISO 8601 format
    } catch (e) {
        console.error('Date formatting error:', e);
        return dateString; // Returns original string if parsing fails
    }
}

// Prepare data before export
function prepareExportData() {
    const exportData = [];
    
    // Fetch all rows from table
    const rows = document.querySelectorAll('#analysesTableBody tr');
    
    rows.forEach(row => {
        // Extract data from row
        const university = row.querySelector('.university-cell').textContent.trim();
        const classification = row.querySelector('.classification-cell').textContent.trim();
        const confidence = parseFloat(row.querySelector('.confidence-cell').textContent.trim()) || 0;
        const uploadDate = row.getAttribute('data-upload_date') || '';
        const analysisDate = row.getAttribute('data-analysis_date') || '';
        const isBaseline = row.classList.contains('baseline-row');
        const filename = row.getAttribute('data-filename') || '';
        const analysisId = row.getAttribute('data-analysis-id') || '';
        
        // Pobieramy tematy (jeśli są dostępne w danych)
        let themes = [];
        const themeElements = row.querySelectorAll('.theme-tag');
        themeElements.forEach(el => themes.push(el.textContent.trim()));
        
        // Dodajemy dane do eksportu
        exportData.push({
            university,
            classification,
            confidence,
            upload_date: uploadDate,
            analysis_date: analysisDate,
            top_themes: themes.join(', '),
            is_baseline: isBaseline,
            filename,
            analysis_id: analysisId
        });
    });
    
    return exportData;
}

// Inicjalizacja nasłuchiwania zdarzeń
document.addEventListener('DOMContentLoaded', function() {
    const exportBtn = document.getElementById('exportAnalysesBtn');
    if (exportBtn) {
        exportBtn.addEventListener('click', function() {
            const exportData = prepareExportData();
            exportAnalysesTable(exportData);
        });
    }
});
