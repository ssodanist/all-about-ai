import { GoogleGenAI } from "@google/genai";
import { AICompany, GroundingChunk } from "../types";

const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });

// Helper to extract JSON from markdown code blocks if present
const cleanJson = (text: string): string => {
  const match = text.match(/```json\n([\s\S]*?)\n```/);
  if (match && match[1]) {
    return match[1];
  }
  return text;
};

// Helper to construct logo URL
const getLogoUrl = (domain: string) => {
    // Using Clearbit for high quality logos
    return `https://logo.clearbit.com/${domain}?size=64`;
};

export const fetchLiveTrends = async (): Promise<AICompany[]> => {
  try {
    const prompt = `
      Analyze current real-time global interest, search volume, and mindshare for the Artificial Intelligence industry using Google Search.

      I am building a "Million Dollar Homepage" style grid composed of AI company logos.
      
      OBJECTIVE:
      Identify the Top 60 (SIXTY) AI companies, tools, and services. 
      Do NOT just list the top 10. I need a long list to fill the grid.
      
      DIVERSITY:
      Include a mix of:
      1. Foundation Models (OpenAI, Anthropic, Google, Meta, Mistral)
      2. Image/Video Gen (Midjourney, Runway, Pika, Luma, Kling, Leonardo, Civitai)
      3. Music/Audio (Suno, Udio, ElevenLabs)
      4. Coding/Productivity (Cursor, Replit, Notion, Jasper, Copy.ai)
      5. Chat/Character (Character.ai, Perplexity, Poe)
      6. Hardware/Infra (Nvidia, Groq, Hugging Face)
      7. New trending startups (Magnific, HeyGen, Harvey, etc.)

      DISTRIBUTION:
      Assign a "share" value (0-100) based on popularity.
      - The Giants (OpenAI, Google) should have large shares (e.g., 10-20).
      - The Long Tail (items 20-60) should have small shares (e.g., 0.5 to 1.0).
      - The sum of all shares MUST be exactly 100.
      
      OUTPUT FORMAT:
      Return a STRICT JSON array.
      Each object must have:
      - "name": string (Company name)
      - "description": string (Very short, 3-6 words max summary)
      - "share": number (The percentage share)
      - "color": string (Dominant brand hex color)
      - "textColor": string (Contrast text color)
      - "domain": string (CRITICAL: The clean website domain, e.g., "openai.com", "suno.com", "midjourney.com" - this is used for logo lookup)
      
      Ensure the output is valid JSON.
    `;

    const response = await ai.models.generateContent({
      model: "gemini-2.5-flash",
      contents: prompt,
      config: {
        tools: [{ googleSearch: {} }],
      },
    });

    const text = response.text || "[]";
    const cleanedText = cleanJson(text);
    
    let companies: Omit<AICompany, 'id' | 'url' | 'logoUrl'>[] = [];
    
    try {
      companies = JSON.parse(cleanedText);
    } catch (e) {
      console.error("Failed to parse GenAI response as JSON", text);
      throw new Error("Failed to parse trends data.");
    }

    // Extract URLs from grounding chunks if available
    const groundingChunks = response.candidates?.[0]?.groundingMetadata?.groundingChunks as GroundingChunk[] | undefined;
    
    // Process and enrich data
    const finalCompanies: AICompany[] = companies.map((c, index) => {
      // Try to find a relevant URL from grounding chunks based on name match
      const matchingChunk = groundingChunks?.find(chunk => 
        chunk.web?.title.toLowerCase().includes(c.name.toLowerCase()) ||
        chunk.web?.uri.toLowerCase().includes(c.name.toLowerCase().replace(/\s/g, ''))
      );

      return {
        ...c,
        id: `trend-${index}-${c.name.toLowerCase().replace(/\s+/g, '-')}`,
        logoUrl: getLogoUrl(c.domain),
        url: matchingChunk?.web?.uri || `https://${c.domain}`
      };
    });

    // Normalize shares to ensure they sum to exactly 100
    const totalShare = finalCompanies.reduce((acc, c) => acc + c.share, 0);
    
    if (totalShare > 0) {
        finalCompanies.forEach(c => {
            c.share = (c.share / totalShare) * 100;
        });
    }

    // Sort by share descending
    return finalCompanies.sort((a, b) => b.share - a.share);

  } catch (error) {
    console.error("Error fetching live trends:", error);
    throw error;
  }
};