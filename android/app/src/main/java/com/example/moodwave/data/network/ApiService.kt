package com.example.moodwave.data.network

import com.example.moodwave.data.network.dto.CatalogItemDto
import com.example.moodwave.data.network.dto.FeedbackRequestDto
import com.example.moodwave.data.network.dto.FeedbackResponseDto
import com.example.moodwave.data.network.dto.HealthDto
import com.example.moodwave.data.network.dto.RecommendRequestDto
import com.example.moodwave.data.network.dto.RecommendResponseDto
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path

interface ApiService {
    @GET("health")
    suspend fun getHealth(): Response<HealthDto>

    @POST("v1/recommend")
    suspend fun getRecommendations(
        @Body body: RecommendRequestDto
    ): Response<RecommendResponseDto>

    @POST("v1/feedback")
    suspend fun postFeedback(
        @Body body: FeedbackRequestDto
    ): Response<FeedbackResponseDto>

    @GET("v1/catalog/{track_id}")
    suspend fun getCatalogItem(
        @Path("track_id") trackId: String
    ): Response<CatalogItemDto>
}
