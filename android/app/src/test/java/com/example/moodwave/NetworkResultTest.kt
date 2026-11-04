package com.example.moodwave

import com.example.moodwave.data.network.ApiService
import com.example.moodwave.data.network.ErrorCategory
import com.example.moodwave.data.network.NetResult
import com.example.moodwave.data.network.NetworkHandler
import com.example.moodwave.data.network.dto.RecommendRequestDto
import kotlinx.coroutines.test.runTest
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import retrofit2.Retrofit
import retrofit2.converter.kotlinx.serialization.asConverterFactory

class NetworkResultTest {

    private lateinit var mockWebServer: MockWebServer
    private lateinit var apiService: ApiService
    private val json = Json {
        ignoreUnknownKeys = true
        isLenient = true
        coerceInputValues = true
    }

    @Before
    fun setUp() {
        mockWebServer = MockWebServer()
        mockWebServer.start()

        val contentType = "application/json".toMediaType()
        val retrofit = Retrofit.Builder()
            .baseUrl(mockWebServer.url("/"))
            .client(OkHttpClient.Builder().build())
            .addConverterFactory(json.asConverterFactory(contentType))
            .build()

        apiService = retrofit.create(ApiService::class.java)
    }

    @After
    fun tearDown() {
        mockWebServer.shutdown()
    }

    @Test
    fun test_health_response_success_parsing() = runTest {
        val jsonBody = """
            {
                "status": "ok",
                "data_loaded": true,
                "feedback_db_ok": true,
                "llm_configured": false,
                "catalog_size": 25000
            }
        """.trimIndent()

        mockWebServer.enqueue(
            MockResponse()
                .setResponseCode(200)
                .setHeader("Content-Type", "application/json")
                .setBody(jsonBody)
        )

        val result = NetworkHandler.safeApiCall { apiService.getHealth() }
        assertTrue("Expected NetResult.Success", result is NetResult.Success)
        val data = (result as NetResult.Success).data
        assertEquals("ok", data.status)
        assertEquals(true, data.dataLoaded)
        assertEquals(true, data.feedbackDbOk)
        assertEquals(false, data.llmConfigured)
        assertEquals(25000, data.catalogSize)
    }

    @Test
    fun test_recommend_degraded_response_mapping() = runTest {
        val jsonBody = """
            {
                "source": "rules",
                "degraded": true,
                "degraded_reason": "rules_fallback",
                "items": []
            }
        """.trimIndent()

        mockWebServer.enqueue(
            MockResponse()
                .setResponseCode(200)
                .setHeader("Content-Type", "application/json")
                .setBody(jsonBody)
        )

        val result = NetworkHandler.safeApiCall {
            apiService.getRecommendations(RecommendRequestDto(query = "calm", userId = "u12345678"))
        }

        assertTrue("Expected NetResult.Degraded", result is NetResult.Degraded)
        val degraded = result as NetResult.Degraded
        assertEquals("rules_fallback", degraded.reason)
        assertEquals(true, degraded.data.degraded)
    }

    @Test
    fun test_rate_limited_response_429() = runTest {
        mockWebServer.enqueue(
            MockResponse()
                .setResponseCode(429)
                .setHeader("Retry-After", "30")
                .setBody("""{"error": "Too Many Requests"}""")
        )

        val result = NetworkHandler.safeApiCall { apiService.getHealth() }
        assertTrue("Expected NetResult.Error", result is NetResult.Error)
        val error = result as NetResult.Error
        assertEquals(ErrorCategory.RateLimited, error.category)
        assertTrue("Message should contain Retry-After value", error.message.contains("30"))
    }

    @Test
    fun test_service_unavailable_503() = runTest {
        mockWebServer.enqueue(
            MockResponse()
                .setResponseCode(503)
                .setBody("""{"error": "Service catalog not loaded"}""")
        )

        val result = NetworkHandler.safeApiCall { apiService.getHealth() }
        assertTrue("Expected NetResult.Error", result is NetResult.Error)
        val error = result as NetResult.Error
        assertEquals(ErrorCategory.NotReady, error.category)
    }

    @Test
    fun test_unknown_json_fields_ignored_without_crash() = runTest {
        val jsonWithUnknownKeys = """
            {
                "status": "ok",
                "data_loaded": true,
                "feedback_db_ok": true,
                "llm_configured": true,
                "catalog_size": 100,
                "unexpected_flag": 9999,
                "future_feature": {
                    "nested_info": "should be ignored"
                }
            }
        """.trimIndent()

        mockWebServer.enqueue(
            MockResponse()
                .setResponseCode(200)
                .setHeader("Content-Type", "application/json")
                .setBody(jsonWithUnknownKeys)
        )

        val result = NetworkHandler.safeApiCall { apiService.getHealth() }
        assertTrue("Expected NetResult.Success", result is NetResult.Success)
        val data = (result as NetResult.Success).data
        assertEquals("ok", data.status)
        assertEquals(100, data.catalogSize)
    }
}
