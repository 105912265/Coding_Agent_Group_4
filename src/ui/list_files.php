
<?php
header("Content-Type: application/json; charset=UTF-8");

$folder = dirname(__DIR__, 2) . "/runtime/workspace";

if (!is_dir($folder)) {
    echo json_encode([]);
    exit;
}

$files = [];

function getFiles($folder, $relativePath = "") {
    global $files;

    foreach (scandir($folder) as $name) {
        if ($name === "." || $name === "..") {
            continue;
        }

        $path = $folder . "/" . $name;
        $relativeFile = $relativePath === ""
            ? $name
            : $relativePath . "/" . $name;

        // Skip symbolic links
        if (is_link($path)) {
            continue;
        }

        if (is_dir($path)) {
            getFiles($path, $relativeFile);
        } elseif (is_file($path)) {

            // Encode each folder/file name separately
            $encodedPath = implode(
                "/",
                array_map("rawurlencode", explode("/", $relativeFile))
            );

            $files[] = [
                "name" => $relativeFile,
                "url" => "serve_file.php/" . $encodedPath
            ];
        }
    }
}

getFiles($folder);

echo json_encode($files);
?>
