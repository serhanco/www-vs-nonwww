const resultsContainer = document.getElementById('results');

async function resolveDnsRecord(domain, type) {
    try {
        const response = await fetch(`https://dns.google/resolve?name=${domain}&type=${type}`);
        const data = await response.json();
        if (data.Answer) {
            if (type === 'A') {
                return data.Answer.map(ans => ans.data).filter(ip => /^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$/.test(ip));
            } else if (type === 'TXT') {
                // TXT records can contain multiple strings, often quoted. Remove quotes.
                return data.Answer.map(ans => ans.data.replace(/"/g, ''));
            }
            return data.Answer.map(ans => ans.data);
        }
        return [];
    } catch (error) {
        // Return a single error string in an array for consistency with success cases
        return [`HATA: ${error.message}`];
    }
}

async function checkDomains(domains) {
    let results = [];

    for (const domain of domains) {
        const nonWwwA = await resolveDnsRecord(domain, 'A');
        const wwwA = await resolveDnsRecord(`www.${domain}`, 'A');
        const cnameRecords = await resolveDnsRecord(domain, 'CNAME');
        const txtRecords = await resolveDnsRecord(domain, 'TXT');

        const nonWwwSet = new Set(nonWwwA);
        const wwwSet = new Set(wwwA);

        let uyumKontroluMetni;
        if (nonWwwSet.size === 0 && wwwSet.size === 0) {
            uyumKontroluMetni = "⚠️ HER İKİSİ DE YOK";
        } else if (nonWwwSet.size > 0 && wwwSet.size === 0) {
            uyumKontroluMetni = "❌ WWW KAYDI YOK";
        } else if (nonWwwSet.size === 0 && wwwSet.size > 0) {
            uyumKontroluMetni = "❌ NON-WWW KAYDI YOK";
        } else if (JSON.stringify([...nonWwwSet].sort()) === JSON.stringify([...wwwSet].sort())) {
            uyumKontroluMetni = "✔️ EŞLEŞİYOR";
        } else {
            uyumKontroluMetni = "🚨 FARKLI IP'ler";
        }

        // CNAME kayıtlarını formatla
        let cnameDisplay;
        if (cnameRecords.length === 0 || (cnameRecords.length === 1 && cnameRecords[0].startsWith('HATA:'))) {
            cnameDisplay = 'YOK';
        } else {
            cnameDisplay = cnameRecords.map(record => 
                record.startsWith('HATA:') ? `❌ ${record}` : `🔗 ${record}`
            ).join('<br>');
        }

        // TXT kayıtlarını formatla
        let txtDisplay;
        if (txtRecords.length === 0 || (txtRecords.length === 1 && txtRecords[0].startsWith('HATA:'))) {
            txtDisplay = 'YOK';
        } else {
            txtDisplay = txtRecords.map(record => 
                record.startsWith('HATA:') ? `❌ ${record}` : `📄 ${record}`
            ).join('<br>');
        }

        results.push({
            'Alan Adı': domain,
            'Non-WWW IP': nonWwwA.join(', ') || 'YOK',
            'WWW IP': wwwA.join(', ') || 'YOK',
            'Uyum Kontrolü': uyumKontroluMetni,
            'CNAME': cnameDisplay,
            'TXT': txtDisplay
        });

        renderTable(results);
    }
}

function renderTable(results) {
    let table = '<table>';
    table += '<tr><th>Alan Adı</th><th>Non-WWW IP</th><th>WWW IP</th><th>Uyum Kontrolü</th><th>CNAME</th><th>TXT</th></tr>';

    for (const item of results) {
        table += `<tr>`;
        table += `<td>${item['Alan Adı']}</td>`;
        table += `<td>${item['Non-WWW IP']}</td>`;
        table += `<td>${item['WWW IP']}</td>`;
        table += `<td>${item['Uyum Kontrolü']}</td>`;
        table += `<td>${item['CNAME']}</td>`;
        table += `<td>${item['TXT']}</td>`;
        table += `</tr>`;
    }

    table += '</table>';
    resultsContainer.innerHTML = table;
}

document.getElementById('domainCheckerForm').addEventListener('submit', async (event) => {
    event.preventDefault();
    const domainListText = document.getElementById('domainList').value;
    const domains = domainListText.split('\n').map(domain => domain.trim()).filter(domain => domain !== '');
    resultsContainer.innerHTML = 'Checking domains...';
    await checkDomains(domains);
});
