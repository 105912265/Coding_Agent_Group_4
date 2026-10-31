
<?php
$folder = realpath(dirname(__DIR__, 2) . "/runtime/workspace");

if ($folder === false) {
    http_response_code(500);
    exit("Workspace not found");
}

// Get the requested file path
$requestedPath = $_SERVER["PATH_INFO"] ?? "";

if ($requestedPath === "") {
    http_response_code(400);
    exit("No file specified");
}

$requestedPath = rawurldecode($requestedPath);
$requestedPath = ltrim(str_replace("\\", "/", $requestedPath), "/");

// Prevent directory traversal
$parts = explode("/", $requestedPath);

foreach ($parts as $part) {
    if ($part === "" || $part === "." || $part === "..") {
        http_response_code(400);
        exit("Invalid file path");
    }
}

$file = realpath($folder . "/" . $requestedPath);

// Make sure the file exists inside the workspace
if ($file === false ||
    !is_file($file) ||
    strpos($file, $folder . DIRECTORY_SEPARATOR) !== 0) {

    http_response_code(404);
    exit("File not found");
}

// Set the correct content type
$extension = strtolower(pathinfo($file, PATHINFO_EXTENSION));

$types = [
    "html" => "text/html; charset=UTF-8",
    "htm" => "text/html; charset=UTF-8",
    "css" => "text/css; charset=UTF-8",
    "js" => "application/javascript; charset=UTF-8",
    "json" => "application/json",
    "txt" => "text/plain; charset=UTF-8",
    "png" => "image/png",
    "jpg" => "image/jpeg",
    "jpeg" => "image/jpeg",
    "gif" => "image/gif",
    "svg" => "image/svg+xml",
    "ico" => "image/x-icon",
    "webp" => "image/webp",
    "woff" => "font/woff",
    "woff2" => "font/woff2",
    "ttf" => "font/ttf",
    "otf" => "font/otf"
];

header("Content-Type: " . ($types[$extension] ?? "application/octet-stream"));

readfile($file);
?>
