package main

import (
	"bufio"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
	"time"

	wappalyzer "github.com/projectdiscovery/wappalyzergo"
)

func main() {
	url := flag.String("url", "", "URL to analyze")
	urls := flag.String("urls", "", "Comma-separated URLs")
	timeout := flag.Int("timeout", 10, "HTTP timeout in seconds")
	jsonOutput := flag.Bool("json", false, "JSON output")
	flag.Parse()

	targets := []string{}
	if *url != "" {
		targets = append(targets, *url)
	}
	if *urls != "" {
		for _, u := range strings.Split(*urls, ",") {
			u = strings.TrimSpace(u)
			if u != "" {
				targets = append(targets, u)
			}
		}
	}
	if len(targets) == 0 {
		scanner := bufio.NewScanner(os.Stdin)
		for scanner.Scan() {
			line := strings.TrimSpace(scanner.Text())
			if line != "" {
				targets = append(targets, line)
			}
		}
	}
	if len(targets) == 0 {
		fmt.Fprintln(os.Stderr, "Usage: wappalyzergo-cli -url <URL> [-json]")
		os.Exit(1)
	}

	wappalyzerClient, err := wappalyzer.New()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}

	client := &http.Client{Timeout: time.Duration(*timeout) * time.Second}

	for _, target := range targets {
		if !strings.HasPrefix(target, "http") {
			target = "https://" + target
		}
		resp, err := client.Get(target)
		if err != nil {
			if *jsonOutput {
				result := map[string]interface{}{"url": target, "error": err.Error()}
				jsonBytes, _ := json.Marshal(result)
				fmt.Println(string(jsonBytes))
			} else {
				fmt.Fprintf(os.Stderr, "Error fetching %s: %v\n", target, err)
			}
			continue
		}
		data, _ := io.ReadAll(resp.Body)
		resp.Body.Close()

		fingerprints := wappalyzerClient.Fingerprint(resp.Header, data)
		fingerprintsWithCats := wappalyzerClient.FingerprintWithCats(resp.Header, data)

		if *jsonOutput {
			result := map[string]interface{}{
				"url":          target,
				"technologies": fingerprints,
				"categories":   fingerprintsWithCats,
			}
			jsonBytes, _ := json.Marshal(result)
			fmt.Println(string(jsonBytes))
		} else {
			fmt.Printf("%s:\n", target)
			for tech := range fingerprints {
				fmt.Printf("  - %s\n", tech)
			}
		}
	}
}
