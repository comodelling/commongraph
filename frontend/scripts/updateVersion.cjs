const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const versionPath = path.join(__dirname, '../../VERSION');
const packageJsonPath = path.join(__dirname, '../package.json');
const packageLockPath = path.join(__dirname, '../package-lock.json');

const version = fs.readFileSync(versionPath, 'utf-8').trim();

// Function to update JSON files
const updateJsonFile = (filePath, newVersion) => {
    const content = JSON.parse(fs.readFileSync(filePath, 'utf-8'));
    if (content.version !== newVersion) {
        content.version = newVersion;
        fs.writeFileSync(filePath, JSON.stringify(content, null, 2));
        console.log(`Updated ${path.basename(filePath)} to version ${newVersion}`);
        return true;
    }
    return false;
};

let updated = false;

// Update package.json if needed
updated = updateJsonFile(packageJsonPath, version) || updated;

// Update package-lock.json if it exists
if (fs.existsSync(packageLockPath)) {
    updated = updateJsonFile(packageLockPath, version) || updated;
} else {
    // If package-lock.json doesn't exist, generate it
    execSync('npm install', { stdio: 'inherit' });
    updated = true;
    console.log('Generated package-lock.json');
}

// Exit with appropriate status
if (updated) {
    console.log('Version update completed.');
    process.exit(1); // Indicate that changes were made
} else {
    console.log('Version is already up-to-date.');
    process.exit(0); // No changes needed
}
