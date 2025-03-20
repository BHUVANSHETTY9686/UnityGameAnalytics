# Unity Integration Guide

This guide explains how to integrate the Game Analytics API with your Unity game.

## Setup

### 1. Add UnityWebRequest Support

Ensure you have the `UnityWebRequest` namespace available in your project (included by default in modern Unity versions).

### 2. Create Analytics Manager Class

Create a new C# script in your Unity project called `AnalyticsManager.cs`:

```csharp
using System;
using System.Collections;
using System.Collections.Generic;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;

public class AnalyticsManager : MonoBehaviour
{
    // Singleton instance
    public static AnalyticsManager Instance { get; private set; }

    [Header("Configuration")]
    [SerializeField] private string apiUrl = "http://localhost:8000/api";
    [SerializeField] private bool enableAnalytics = true;
    [SerializeField] private bool logToConsole = true;

    // Session data
    private string sessionId;
    private string playerId;
    private DateTime sessionStartTime;

    private void Awake()
    {
        // Singleton pattern
        if (Instance != null && Instance != this)
        {
            Destroy(gameObject);
            return;
        }
        
        Instance = this;
        DontDestroyOnLoad(gameObject);
        
        // Generate unique player ID if not already set
        if (string.IsNullOrEmpty(playerId))
        {
            playerId = PlayerPrefs.GetString("AnalyticsPlayerId", "");
            if (string.IsNullOrEmpty(playerId))
            {
                playerId = Guid.NewGuid().ToString();
                PlayerPrefs.SetString("AnalyticsPlayerId", playerId);
                PlayerPrefs.Save();
            }
        }
    }

    private void OnEnable()
    {
        StartNewSession();
    }

    private void OnDisable()
    {
        EndCurrentSession();
    }

    private void OnApplicationQuit()
    {
        EndCurrentSession();
    }
    
    private void OnApplicationPause(bool pauseStatus)
    {
        if (pauseStatus)
        {
            EndCurrentSession();
        }
        else
        {
            StartNewSession();
        }
    }

    #region Public API

    /// <summary>
    /// Starts a new analytics session
    /// </summary>
    public void StartNewSession()
    {
        if (!enableAnalytics) return;
        
        sessionId = Guid.NewGuid().ToString();
        sessionStartTime = DateTime.UtcNow;
        
        StartCoroutine(StartSession());
    }

    /// <summary>
    /// Ends the current analytics session
    /// </summary>
    public void EndCurrentSession()
    {
        if (!enableAnalytics || string.IsNullOrEmpty(sessionId)) return;
        
        StartCoroutine(EndSession());
    }

    /// <summary>
    /// Records a gameplay event
    /// </summary>
    /// <param name="eventType">Category of event (e.g., "Achievement", "LevelComplete")</param>
    /// <param name="eventName">Specific event name</param>
    /// <param name="levelId">Optional level identifier</param>
    /// <param name="position">Optional player position</param>
    /// <param name="details">Optional additional details</param>
    public void LogEvent(string eventType, string eventName, string levelId = null, Vector3? position = null, Dictionary<string, object> details = null)
    {
        if (!enableAnalytics || string.IsNullOrEmpty(sessionId)) return;
        
        StartCoroutine(SendEvent(eventType, eventName, levelId, position, details));
    }

    /// <summary>
    /// Records a numerical gameplay metric
    /// </summary>
    /// <param name="metricName">Name of the metric</param>
    /// <param name="value">Numerical value</param>
    /// <param name="levelId">Optional level identifier</param>
    public void LogMetric(string metricName, float value, string levelId = null)
    {
        if (!enableAnalytics || string.IsNullOrEmpty(sessionId)) return;
        
        StartCoroutine(SendMetric(metricName, value, levelId));
    }

    #endregion

    #region API Requests

    private IEnumerator StartSession()
    {
        string deviceInfo = $"{SystemInfo.deviceModel} | {SystemInfo.operatingSystem} | {Application.version}";
        
        Dictionary<string, object> data = new Dictionary<string, object>
        {
            { "session_id", sessionId },
            { "player_id", playerId },
            { "device_info", deviceInfo }
        };
        
        string jsonData = JsonUtility.ToJson(new JsonSerializationWrapper(data));
        
        using (UnityWebRequest request = CreatePostRequest($"{apiUrl}/sessions/start", jsonData))
        {
            yield return request.SendWebRequest();
            
            if (request.result != UnityWebRequest.Result.Success)
            {
                LogError("Failed to start session: " + request.error);
                yield break;
            }
            
            LogMessage("Session started: " + sessionId);
        }
    }

    private IEnumerator EndSession()
    {
        Dictionary<string, object> data = new Dictionary<string, object>
        {
            { "session_id", sessionId },
            { "end_time", DateTime.UtcNow.ToString("o") }
        };
        
        string jsonData = JsonUtility.ToJson(new JsonSerializationWrapper(data));
        
        using (UnityWebRequest request = CreatePostRequest($"{apiUrl}/sessions/end", jsonData))
        {
            yield return request.SendWebRequest();
            
            if (request.result != UnityWebRequest.Result.Success)
            {
                LogError("Failed to end session: " + request.error);
                yield break;
            }
            
            LogMessage("Session ended: " + sessionId);
            sessionId = null;
        }
    }

    private IEnumerator SendEvent(string eventType, string eventName, string levelId, Vector3? position, Dictionary<string, object> details)
    {
        Dictionary<string, object> data = new Dictionary<string, object>
        {
            { "session_id", sessionId },
            { "event_type", eventType },
            { "event_name", eventName },
            { "timestamp", DateTime.UtcNow.ToString("o") }
        };
        
        if (!string.IsNullOrEmpty(levelId))
        {
            data["level_id"] = levelId;
        }
        
        if (position.HasValue)
        {
            data["position_x"] = position.Value.x;
            data["position_y"] = position.Value.y;
            data["position_z"] = position.Value.z;
        }
        
        if (details != null && details.Count > 0)
        {
            data["details"] = details;
        }
        
        string jsonData = JsonUtility.ToJson(new JsonSerializationWrapper(data));
        
        using (UnityWebRequest request = CreatePostRequest($"{apiUrl}/events", jsonData))
        {
            yield return request.SendWebRequest();
            
            if (request.result != UnityWebRequest.Result.Success)
            {
                LogError($"Failed to log event {eventName}: " + request.error);
            }
            else
            {
                LogMessage($"Event logged: {eventType}.{eventName}");
            }
        }
    }

    private IEnumerator SendMetric(string metricName, float value, string levelId)
    {
        Dictionary<string, object> data = new Dictionary<string, object>
        {
            { "session_id", sessionId },
            { "metric_name", metricName },
            { "metric_value", value },
            { "timestamp", DateTime.UtcNow.ToString("o") }
        };
        
        if (!string.IsNullOrEmpty(levelId))
        {
            data["level_id"] = levelId;
        }
        
        string jsonData = JsonUtility.ToJson(new JsonSerializationWrapper(data));
        
        using (UnityWebRequest request = CreatePostRequest($"{apiUrl}/metrics", jsonData))
        {
            yield return request.SendWebRequest();
            
            if (request.result != UnityWebRequest.Result.Success)
            {
                LogError($"Failed to log metric {metricName}: " + request.error);
            }
            else
            {
                LogMessage($"Metric logged: {metricName} = {value}");
            }
        }
    }

    private UnityWebRequest CreatePostRequest(string url, string jsonData)
    {
        UnityWebRequest request = new UnityWebRequest(url, "POST");
        byte[] bodyRaw = Encoding.UTF8.GetBytes(jsonData);
        request.uploadHandler = new UploadHandlerRaw(bodyRaw);
        request.downloadHandler = new DownloadHandlerBuffer();
        request.SetRequestHeader("Content-Type", "application/json");
        return request;
    }

    #endregion

    #region Utilities

    private void LogMessage(string message)
    {
        if (logToConsole)
        {
            Debug.Log($"[Analytics] {message}");
        }
    }

    private void LogError(string message)
    {
        if (logToConsole)
        {
            Debug.LogError($"[Analytics] {message}");
        }
    }

    #endregion

    // Helper class for JSON serialization
    [Serializable]
    private class JsonSerializationWrapper
    {
        public string json;

        public JsonSerializationWrapper(Dictionary<string, object> data)
        {
            json = "{";
            int i = 0;
            foreach (var kvp in data)
            {
                if (i > 0) json += ",";
                
                if (kvp.Value is string stringValue)
                {
                    json += $"\"{kvp.Key}\":\"{stringValue}\"";
                }
                else if (kvp.Value is Dictionary<string, object> dictValue)
                {
                    json += $"\"{kvp.Key}\":{JsonUtility.ToJson(new JsonSerializationWrapper(dictValue))}";
                }
                else
                {
                    json += $"\"{kvp.Key}\":{kvp.Value}";
                }
                
                i++;
            }
            json += "}";
        }
    }
}
```

### 3. Set Up the Analytics Manager in Your Game

1. Create an empty GameObject in your main scene
2. Add the `AnalyticsManager` script to it
3. Configure the API URL to point to your deployed analytics server

### 4. Usage Examples

#### Track Session Start/End

The AnalyticsManager automatically tracks sessions, but you can also manually control them:

```csharp
// Start a new session
AnalyticsManager.Instance.StartNewSession();

// End the current session
AnalyticsManager.Instance.EndCurrentSession();
```

#### Log Gameplay Events

```csharp
// Simple event
AnalyticsManager.Instance.LogEvent("Achievement", "FirstKill");

// Event with level information
AnalyticsManager.Instance.LogEvent("LevelComplete", "Level1", "level_01");

// Event with position
Vector3 playerPosition = player.transform.position;
AnalyticsManager.Instance.LogEvent("Death", "EnemyContact", "level_02", playerPosition);

// Event with additional details
Dictionary<string, object> details = new Dictionary<string, object>
{
    { "weapon", "laser_gun" },
    { "enemy_type", "boss" },
    { "difficulty", "hard" }
};
AnalyticsManager.Instance.LogEvent("Combat", "EnemyDefeated", "level_03", null, details);
```

#### Log Gameplay Metrics

```csharp
// Track score
AnalyticsManager.Instance.LogMetric("Score", 12500f, "level_01");

// Track time
AnalyticsManager.Instance.LogMetric("CompletionTimeSeconds", 145.5f, "level_02");

// Track resources
AnalyticsManager.Instance.LogMetric("AmmoRemaining", 42f);
AnalyticsManager.Instance.LogMetric("HealthPercentage", 75.3f);
```

## Batch Processing

For performance-critical games, consider implementing a local queue to batch send analytics events at appropriate times rather than sending each event immediately.

## Network Considerations

- Include error handling for when the device is offline
- Consider adding retry logic for failed requests
- Implement a local cache for offline analytics that can be sent when connectivity is restored

## Security Considerations

For production deployment, you may want to:
1. Add an API key to secure your endpoints
2. Use HTTPS for all communications
3. Implement rate limiting to prevent abuse
