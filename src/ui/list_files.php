<?php
header("Content-Type: application/json; charset=UTF-8");

$folder = __DIR__ . "/project1";
$urlFolder = "project1";

if (!is_dir($folder)) {
    http_response_code(404);
    echo json_encode([]);
    exit;
}

$files = [];

foreach (scandir($folder) as $name) {
    if ($name === "." || $name === "..") {
        continue;
    }

    $path = $folder . "/" . $name;

    if (is_file($path) && !is_link($path)) {
        $files[] = [
            "name" => $name,
            "url" => $urlFolder . "/" . rawurlencode($name)
        ];
    }
}

echo json_encode($files);