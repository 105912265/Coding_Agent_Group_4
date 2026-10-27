
<?php
$folder = dirname(__DIR__, 2) . "/runtime/workspace";

if (!isset($_GET["path"])) {
    http_response_code(400);
    exit("No file specified");
}

$name = basename($_GET["path"]);
$file = $folder . "/" . $name;

if (!is_file($file) || is_link($file)) {
    http_response_code(404);
    exit("File not found");
}

$extension = strtolower(pathinfo($file, PATHINFO_EXTENSION));

$types = [
    "html" => "text/html",
    "htm" => "text/html",
    "css" => "text/css",
    "js" => "application/javascript",
    "json" => "application/json",
    "txt" => "text/plain",
    "png" => "image/png",
    "jpg" => "image/jpeg",
    "jpeg" => "image/jpeg",
    "gif" => "image/gif",
    "svg" => "image/svg+xml",
    "ico" => "image/x-icon"
];

header("Content-Type: " . ($types[$extension] ?? "application/octet-stream"));
readfile($file);
?>
