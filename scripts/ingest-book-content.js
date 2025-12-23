const fs = require('fs').promises;
const path = require('path');
const axios = require('axios');

// Configuration
const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000';
const DOCUMENT_ID_PREFIX = 'textbook';

async function readMarkdownFiles(dirPath) {
    const entries = await fs.readdir(dirPath, { withFileTypes: true });
    let files = [];

    for (let entry of entries) {
        const fullPath = path.join(dirPath, entry.name);

        if (entry.isDirectory()) {
            const nestedFiles = await readMarkdownFiles(fullPath);
            files = files.concat(nestedFiles);
        } else if (entry.isFile() && path.extname(entry.name) === '.md') {
            files.push(fullPath);
        }
    }

    return files;
}

async function ingestContent() {
    console.log('Starting textbook content ingestion...');

    try {
        // Find all markdown files in the docs directory
        const docsPath = path.join(__dirname, '..', 'website', 'docs');
        const markdownFiles = await readMarkdownFiles(docsPath);

        console.log(`Found ${markdownFiles.length} markdown files to ingest`);

        for (const filePath of markdownFiles) {
            console.log(`Processing: ${filePath}`);

            try {
                // Read the content of the markdown file
                const content = await fs.readFile(filePath, 'utf8');

                // Extract document ID from file path
                const relativePath = path.relative(docsPath, filePath);
                const documentId = `${DOCUMENT_ID_PREFIX}-${relativePath.replace(/[\/\\]/g, '-').replace('.md', '')}`;

                // Prepare the ingestion request
                const ingestionData = {
                    content: content,
                    document_id: documentId,
                    source_url: `/docs/${relativePath}`,
                    metadata: {
                        title: path.basename(filePath, '.md'),
                        source_path: relativePath,
                        file_type: 'markdown',
                        chapter: path.dirname(relativePath).split(path.sep).pop() || 'root'
                    }
                };

                console.log(`Ingesting document: ${documentId}`);

                // Send the content to the backend ingestion API
                const response = await axios.post(
                    `${API_BASE_URL}/api/v1/ingest`,
                    ingestionData,
                    {
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        timeout: 30000 // 30 second timeout
                    }
                );

                console.log(`Successfully ingested: ${documentId} - ${response.data.message}`);

                // Add a small delay between requests to avoid overwhelming the server
                await new Promise(resolve => setTimeout(resolve, 500));

            } catch (error) {
                console.error(`Error ingesting file ${filePath}:`, error.response?.data || error.message);
            }
        }

        console.log('Content ingestion completed!');

    } catch (error) {
        console.error('Error during content ingestion:', error.message);
        process.exit(1);
    }
}

// Run the ingestion process
if (require.main === module) {
    ingestContent();
}

module.exports = { readMarkdownFiles, ingestContent };