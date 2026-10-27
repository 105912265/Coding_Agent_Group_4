
<?php
// only allow reset requests sent by POST
if ($_SERVER["REQUEST_METHOD"] != "POST") {
    header("Location: index.php");
    exit;
}

// locate the project folders
$projectFolder = dirname(__DIR__, 2);
$uiFolder = __DIR__;
$workspaceFolder = $projectFolder . "/runtime/workspace";

// files to clear
$files = [
    $uiFolder . "/messages.txt",
    $uiFolder . "/errors.txt",
    $uiFolder . "/agent_output.log",
    $uiFolder . "/pending_prompt.txt"
];

// clear the text files
foreach ($files as $file) {
    if (file_exists($file) && is_file($file)) {
        file_put_contents($file, "");
    }
}

// reset the project status
file_put_contents(
    $uiFolder . "/status.txt",
    "TITLE|New Project\nSTAGE|Ready\nPROGRESS|0\n"
);

// delete generated workspace contents, but keep the workspace folder
function clearFolder($folder) {
    if (!is_dir($folder) || is_link($folder)) {
        return;
    }

    $items = scandir($folder);

    foreach ($items as $item) {
        if ($item == "." || $item == "..") {
            continue;
        }

        $path = $folder . DIRECTORY_SEPARATOR . $item;

        // do not follow symbolic links
        if (is_link($path) || is_file($path)) {
            unlink($path);
        } elseif (is_dir($path)) {
            clearFolder($path);
            rmdir($path);
        }
    }
}

if (is_dir($workspaceFolder)) {
    clearFolder($workspaceFolder);
}

header("Location: index.php");
exit;
?>
