import asyncio
import edge_tts

async def main():
    voices = await edge_tts.list_voices()
    pt_br = [v for v in voices if v['Locale'] == 'pt-BR']
    print(f"Found {len(pt_br)} pt-BR voices:")
    for v in pt_br:
        print(f"  - {v['ShortName']} ({v['Gender']})")

if __name__ == '__main__':
    asyncio.run(main())
