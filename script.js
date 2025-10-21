const resultsContainer = document.getElementById('results');

async function resolveDomain(domain) {
    try {
        const response = await fetch(`https://dns.google/resolve?name=${domain}&type=A`);
        const data = await response.json();
        if (data.Answer) {
            return data.Answer.map(ans => ans.data).filter(ip => /^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$/.test(ip));
        }
        return [];
    } catch (error) {
        return [`HATA: ${error.message}`];
    }
}


async function checkDomains(domains) {
    let results = [];

    for (const domain of domains) {
        const nonWwwA = await resolveDomain(domain);
        const wwwA = await resolveDomain(`www.${domain}`);

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

        results.push({
            'Alan Adı': domain,
            'Non-WWW IP': nonWwwA.join(', ') || 'YOK',
            'WWW IP': wwwA.join(', ') || 'YOK',
            'Uyum Kontrolü': uyumKontroluMetni
        });

        renderTable(results);
    }
}

function renderTable(results) {
    let table = '<table>';
    table += '<tr><th>Alan Adı</th><th>Non-WWW IP</th><th>WWW IP</th><th>Uyum Kontrolü</th></tr>';

    for (const item of results) {
        table += `<tr>`;
        table += `<td>${item['Alan Adı']}</td>`;
        table += `<td>${item['Non-WWW IP']}</td>`;
        table += `<td>${item['WWW IP']}</td>`;
        table += `<td>${item['Uyum Kontrolü']}</td>`;
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