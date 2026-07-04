const express = require('express');
const fs = require('fs');
const path = require('path');

const app = express();
app.use(express.json());

const fixtures = path.resolve(__dirname, 'fixtures');
let currentScenario = 'happy-path';
const scenarios = {
  'happy-path': () => ({
    sitemap: fs.readFileSync(path.join(fixtures, 'sitemap.xml'), 'utf8'),
    robots: fs.readFileSync(path.join(fixtures, 'robots.txt'), 'utf8'),
  }),
};

app.post('/__scenario__', (req, res) => {
  const { scenario } = req.body;
  if (!scenario || !scenarios[scenario]) {
    return res.status(400).json({ error: 'unknown scenario' });
  }
  currentScenario = scenario;
  res.json({ scenario });
});

app.get('/robots.txt', (req, res) => {
  res.type('text/plain');
  res.send(scenarios[currentScenario]().robots);
});

app.get('/sitemap.xml', (req, res) => {
  res.type('application/xml');
  res.send(scenarios[currentScenario]().sitemap);
});

app.get('/pages/:name', (req, res) => {
  const page = req.params.name;
  const filePath = path.join(fixtures, 'pages', page);
  if (!fs.existsSync(filePath)) {
    return res.status(404).send('not found');
  }
  res.type('text/html');
  res.send(fs.readFileSync(filePath, 'utf8'));
});

app.listen(8080, () => {
  console.log('testserver listening on http://127.0.0.1:8080');
});
