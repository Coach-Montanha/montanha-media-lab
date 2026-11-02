import asyncio
import edge_tts

async def test_invalid_voice():
    try:
        c = edge_tts.Communicate("Olá", "pt-BR-BrendaNeural")
        await c.save("test_brenda.mp3")
        print("SUCCESS with Brenda")
    except Exception as e:
        print("FAILED with Brenda:", type(e), e)

async def test_valid_voices():
    for v in ["pt-BR-FranciscaNeural", "pt-BR-AntonioNeural", "pt-BR-ThalitaMultilingualNeural"]:
        try:
            c = edge_tts.Communicate("Olá", v, rate="+10%", pitch="+2Hz")
            await c.save(f"test_{v}.mp3")
            print(f"SUCCESS with {v}")
        except Exception as e:
            print(f"FAILED with {v}:", type(e), e)

async def main():
    await test_invalid_voice()
    await test_valid_voices()

if __name__ == "__main__":
    asyncio.run(main())
