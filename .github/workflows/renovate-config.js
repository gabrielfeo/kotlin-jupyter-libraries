// const fs = require('fs');
// const configFilePath = "P:\\projects\\workspace\\net.twisterrob.gradle\\.github\\renovate.json";
// const configFileText = fs.readFileSync(configFilePath, "utf8");
module.exports = {
	"dryRun": "extract",
	"logFile": "/tmp/renovate.log",
	"logFileLevel": "info",
	"repositories": ["gabrielfeo/kotlin-jupyter-libraries"],
//	"logFormat": "text",
};
