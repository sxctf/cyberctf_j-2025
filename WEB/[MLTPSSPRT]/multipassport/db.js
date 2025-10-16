const sqlite3 = require("sqlite3").verbose();
const crypto = require("crypto");

const databaseFilename = "./sqlite.db";
const db = new sqlite3.Database(databaseFilename);

const sites = `CREATE TABLE IF NOT EXISTS sites (
    id TEXT PRIMARY KEY NOT NULL,
    html TEXT NOT NULL,
    owner integer NOT NULL
);`;

const test_passport = `
    <div class="passport">
        <div class="holo-stamp"></div>
        <div class="header">
            <h1>МУЛЬТИПАСПОРТ</h1>
            <p>ФЕДЕРАЦИЯ ПЛАНЕТ • ГАЛАКТИЧЕСКИЙ СОЮЗ</p>
        </div>

        <div class="content">
            <div class="photo">
                [ГРАВАТАР-ИДЕНТИФИКАТОР]
            </div>
            <div class="details">
                <div class="detail-row">
                    <div class="detail-label">ИМЯ:</div>
                    <div class="detail-value">ПРОВЕРКИН АДМИН ТЕСТОВИЧ</div>
                </div>
                <div class="detail-row">
                    <div class="detail-label">ПЛАНЕТА:</div>
                    <div class="detail-value">ЗЕМЛЯ</div>
                </div>
                <div class="detail-row">
                    <div class="detail-label">СРОК ДЕЙСТВИЯ:</div>
                    <div class="detail-value">∞</div>
                </div>
            </div>
        </div>
    </div>`

db.serialize(() => {
    db.run(sites);
    db.get('SELECT * FROM sites WHERE id = ?', ['test_passport'], (err, row) => {
        if (!row) {
            db.run(
                'INSERT INTO sites (id, html, owner) VALUES (?, ?, ?)',
                [
                    'test_passport',
                    test_passport,
                    -1
                ]
            );
        }
    });
});

function createSite(html, owner = {}) {
    return new Promise((resolve, reject) => {
        const id = crypto.randomBytes(16).toString('hex');
        db.run(
            'INSERT INTO sites (id, html, owner) VALUES (?, ?, ?)',

            [id, html, owner],
            function (err) {
                if (err) return reject(err);
                resolve({ id });
            }
        );
    });
}

function getSiteById(id) {
    return new Promise((resolve, reject) => {
        db.get('SELECT * FROM sites WHERE id = ?', [id], (err, row) => {
            if (err) return reject(err);
            resolve(row);
        });
    });
}

module.exports = {
    db,
    createSite,
    getSiteById,
};