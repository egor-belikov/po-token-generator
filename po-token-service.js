const express = require('express');
const { PoTokenGenerator } = require('pytubefix');

const app = express();
app.use(express.json());

const port = process.env.PORT || 3000;

app.post('/generate-po-token', async (req, res) => {
    try {
        const { video_id } = req.body;
        
        if (!video_id) {
            return res.status(400).json({ error: 'Missing video_id parameter' });
        }
        
        const poToken = await PoTokenGenerator.generate(video_id);
        res.json({ po_token: poToken });
    } catch (error) {
        console.error('Error generating PoToken:', error);
        res.status(500).json({ error: 'Failed to generate PoToken' });
    }
});

app.get('/', (req, res) => {
    res.send('PoToken Generator Service is running');
});

app.listen(port, () => {
    console.log(`Server running on port ${port}`);
});