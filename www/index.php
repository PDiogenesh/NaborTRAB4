<!DOCTYPE html>
<html>
<head>
    <title>Link Extractor</title>
</head>
<body>
    <h1>Link Extractor</h1>
    <form method="GET">
        <input type="text" name="url" placeholder="Enter URL (e.g. http://google.com)" size="50" required>
        <button type="submit">Extract Links</button>
    </form>

    <?php
    if (isset($_GET['url'])) {
        $url = $_GET['url'];
        $api_host = getenv('API_HOST') ?: 'linkextractor';
        $api_port = getenv('API_PORT') ?: '5000';
        
        $api_url = "http://$api_host:$api_port/api/extract?url=" . urlencode($url);
        
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $api_url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        $response = curl_exec($ch);
        $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        if ($http_code == 200) {
            $data = json_decode($response, true);
            echo "<h2>Links for: " . htmlspecialchars($data['url']) . "</h2>";
            echo "<ul>";
            foreach ($data['links'] as $link) {
                echo "<li><a href=\"" . htmlspecialchars($link['href']) . "\">" . htmlspecialchars($link['text'] ?: $link['href']) . "</a></li>";
            }
            echo "</ul>";
        } else {
            echo "<p style='color: red;'>Error: " . htmlspecialchars($response) . "</p>";
        }
    }
    ?>
</body>
</html>
