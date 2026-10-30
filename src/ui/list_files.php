
<?php
header("Content-Type: application/json; charset=UTF-8");

$folder = dirname(__DIR__, 2) . "/runtime/workspace";

if (!is_dir($folder)) {
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
            "url" => "serve_file.php?path=" . rawurlencode($name)
        ];
    }
}

echo json_encode($files);
?>
