package com.example.moodwave.data.network

import com.example.moodwave.data.network.dto.RecommendResponseDto
import retrofit2.Response
import java.io.IOException
import java.net.ConnectException
import java.net.SocketTimeoutException
import java.net.UnknownHostException

enum class ErrorCategory {
    Offline,
    Timeout,
    ServerDown,
    BadInput,
    RateLimited,
    NotReady,
    Unknown
}

sealed class NetResult<out T> {
    data class Success<out T>(val data: T) : NetResult<T>()
    data class Degraded<out T>(val data: T, val reason: String?) : NetResult<T>()
    data class Error(val category: ErrorCategory, val message: String) : NetResult<Nothing>()
}

object NetworkHandler {
    suspend fun <T> safeApiCall(apiCall: suspend () -> Response<T>): NetResult<T> {
        return try {
            val response = apiCall()
            handleResponse(response)
        } catch (e: Throwable) {
            handleException(e)
        }
    }

    fun <T> handleResponse(response: Response<T>): NetResult<T> {
        if (response.isSuccessful) {
            val body = response.body()
            return if (body != null) {
                if (body is RecommendResponseDto && body.degraded) {
                    NetResult.Degraded(body, body.degradedReason)
                } else {
                    NetResult.Success(body)
                }
            } else {
                NetResult.Error(ErrorCategory.Unknown, "Empty response body received.")
            }
        }

        val code = response.code()
        return when (code) {
            400, 422 -> NetResult.Error(
                ErrorCategory.BadInput,
                "Request was rejected due to invalid input."
            )
            429 -> {
                val retryAfter = response.headers()["Retry-After"] ?: "a short delay"
                NetResult.Error(
                    ErrorCategory.RateLimited,
                    "Too many requests. Retry after $retryAfter."
                )
            }
            503 -> NetResult.Error(
                ErrorCategory.NotReady,
                "Service catalog or models are not yet loaded."
            )
            in 500..599 -> NetResult.Error(
                ErrorCategory.ServerDown,
                "Internal server error. Please try again later."
            )
            else -> NetResult.Error(
                ErrorCategory.Unknown,
                "HTTP transaction failed with status code $code."
            )
        }
    }

    fun handleException(throwable: Throwable): NetResult<Nothing> {
        return when (throwable) {
            is SocketTimeoutException -> NetResult.Error(
                ErrorCategory.Timeout,
                "Connection timed out waiting for backend response."
            )
            is UnknownHostException, is ConnectException -> NetResult.Error(
                ErrorCategory.Offline,
                "Backend server unreachable. Verify network or host server."
            )
            is IOException -> NetResult.Error(
                ErrorCategory.Offline,
                "Network I/O error occurred. Check internet connectivity."
            )
            else -> NetResult.Error(
                ErrorCategory.Unknown,
                "An unexpected application error occurred."
            )
        }
    }
}
