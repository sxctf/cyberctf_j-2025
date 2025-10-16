const express = require('express');
const puppeteer = require('puppeteer');
const crypto = require('crypto');
const cookieParser = require('cookie-parser');
const db = require('./db');

const app = express();
const sessionRouter = express.Router();
const adminRouter = express.Router();
const FLAG = process.env.FLAG || 'flag{THIS_IS_FAKE_FLAG}'
sessionRouter.use(cookieParser());
adminRouter.use(cookieParser());

app.use(express.urlencoded({ extended: true }));
app.use(express.static(__dirname + '/views'));
app.use(function(err, req, res, next) {
    console.error(err.stack);
    res.status(500).send('Something broke!');
});

hosting_template = `<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    {{CSP}}
    <title>Мультипаспорт Федерации Планет</title>
    <link rel="stylesheet" href="/styles.css">
</head>
<body>
    {{site.html}}
    <div class="footer">
        <p>● НАРУШЕНИЕ МЕЖГАЛАКТИЧЕСКОГО АКТА 17-Ω КАРАЕТСЯ ИЗГНАНИЕМ В HYPERVISOR ●</p>
    </div>
    {{button}}
</body>
</html>`

app.use('/public', sessionRouter);
app.use('/admin', adminRouter);

function parseCookies(cookieHeader) {
    const cookies = new Map();
    if (!cookieHeader) return cookies;

    let pos = 0;
    while (pos < cookieHeader.length) {
        while (pos < cookieHeader.length && cookieHeader[pos] === ' ') pos++;
        if (pos >= cookieHeader.length) break;

        const nameStart = pos;
        while (pos < cookieHeader.length && cookieHeader[pos] !== '=' && cookieHeader[pos] !== ' ') pos++;
        const name = cookieHeader.slice(nameStart, pos);

        while (pos < cookieHeader.length && cookieHeader[pos] !== '=') pos++;
        if (pos >= cookieHeader.length) {
            cookies.set(name, '');
            break;
        }
        pos++;

        let value;
        if (pos < cookieHeader.length && cookieHeader[pos] === '"') {
            pos++;
            const valueStart = pos;
            while (pos < cookieHeader.length && cookieHeader[pos] !== '"') pos++;
            value = cookieHeader.slice(valueStart, pos);
            if (pos < cookieHeader.length) pos++;
        } else {
            const valueStart = pos;
            while (pos < cookieHeader.length && cookieHeader[pos] !== ';' && cookieHeader[pos] !== ' ') pos++;
            value = cookieHeader.slice(valueStart, pos);
        }

        cookies.set(name, value);

        while (pos < cookieHeader.length && cookieHeader[pos] !== ';') pos++;
        pos++;
    }

    return cookies;
}

function setCookiesWithHttpOnly(res, cookies) {
    cookies.forEach((value, name) => {
        console.log(`${name} : ${value}`);
        if (name === "SESSION" || name === "FLAG") {
            res.cookie(name, value, {
                httpOnly: true,
                sameSite: 'strict',
            });
        } else {
            res.cookie(name, value, {
                httpOnly: false,
                sameSite: 'strict',
            });
        }
    });
}

sessionRouter.use(async function(req, res, next) {
    cookies = parseCookies(req.headers.cookie);

    if (!cookies.has("SESSION")) {
        req.cookies.SESSION = crypto.randomBytes(16).toString('hex');
        cookies.set("SESSION", req.cookies.SESSION);
    }

    setCookiesWithHttpOnly(res, cookies);
    next();
});

adminRouter.use(async function(req, res, next) {
    cookies = parseCookies(req.headers.cookie);

    if (cookies.has("FLAG")) {
        if (cookies.get("FLAG") === FLAG) {
            setCookiesWithHttpOnly(res, cookies);
            next();
        } else {
            res.status(401).send('Нет доступа');
        }
    } else {
        res.status(401).send('Вы не авторизованы');
    }
});

sessionRouter.get('/review/:siteId', async (req, res) => {
    try {
        const browser = await puppeteer.launch({args: ['--no-sandbox']});
        const page = await browser.newPage();

        await browser.setCookie(
          {
            name: 'FLAG',
            value: FLAG,
            domain: 'localhost',
            path: '/',
            httpOnly: true,
            secure: false,
          },
        );
        
        await page.goto(`http://localhost:1337/admin/site/${req.params.siteId}`);
        await new Promise(resolve => setTimeout(resolve, 1000));
        await page.waitForFunction('true');
        const htmlContent = await page.content();

        // Админ работает
        await new Promise(r => setTimeout(r, 5000));

        await browser.close();
        res.send("Проверка Мультипаспорта завершена");
    } catch(e) {console.error(e); res.send("Технические неполадки")}
});

sessionRouter.post('/upload', async (req, res) => {
    const html = req.body.html;
    if (typeof html !== 'string' || html.length < 1 || html.length > 65536) {
        return res.status(400).json({ error: 'Невалидный Мультипаспорт' });
    }

    try {
        const owner = req.cookies["SESSION"];
        const { id } = await db.createSite(html, owner);
        res.redirect(`/public/site/${id}`);
    } catch (e) {
        res.status(500).json({ error: 'Не удалось отправить Мультипаспорт' });
    }
});

sessionRouter.get('/site/:id', async (req, res) => {
    try {
        const site = await db.getSiteById(req.params.id);
        if (!site) return res.status(404).send('Not found');

        res.setHeader('Content-Type', 'text/html; charset=utf-8');
        if ((!req.cookies["SESSION"] || req.cookies["SESSION"].toString() !== site.owner.toString()) && (!req.cookies["FLAG"] || req.cookies["FLAG"].toString() !== FLAG)) {
            return res.status(403).send('Это не ваш Мультипаспорт');
        }
        
        CSP = '<meta http-equiv="Content-Security-Policy" content="default-src * \'unsafe-inline\'">';
        button = `<form id="reviewForm" action="/public/review/${site.id}" method="GET">
            <button type="submit">Отправить на проверку</button>
        </form>`

        html = hosting_template
            .replaceAll("{{site.html}}", site.html || 'Мультипаспорт не найден')
            .replaceAll("{{site.id}}", site.id || 'ID не найден')
            .replaceAll("{{CSP}}", CSP)
            .replaceAll("{{button}}", button);

        res.send(html);
    } catch (e) {
        console.error(e);
        res.status(500).send('Internal error');
    }
});

adminRouter.get('/site/:id', async (req, res) => {
    try {
        const site = await db.getSiteById(req.params.id);
        if (!site) return res.status(404).send('Not found');

        res.setHeader('Content-Type', 'text/html; charset=utf-8');
        CSP = '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'">';
        html = hosting_template
            .replaceAll("{{site.html}}", site.html || 'Мультипаспорт не найден')
            .replaceAll("{{site.id}}", site.id || 'ID не найден')
            .replaceAll("{{CSP}}", CSP)
            .replaceAll("{{button}}", "");

        res.send(html);
    } catch (e) {
        console.error(e);
        res.status(500).send('Технические неполадки');
    }
});

sessionRouter.get('/', (req, res) => {
    res.sendFile(__dirname + '/views/index.html');
});

app.listen(1337, () => console.log('listening on http://localhost:1337'));