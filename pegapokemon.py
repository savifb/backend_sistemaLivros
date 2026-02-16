import asyncio
import random
import time

# Listas de Pokémons por região
POKEMONS_KANTO = ["Pikachu", "Charmander", "Bulbasaur", "Squirtle", "Eevee", "Mewtwo", "Dragonite"]
POKEMONS_JOHTO = ["Chikorita", "Cyndaquil", "Totodile", "Pichu", "Lugia", "Ho-Oh", "Umbreon"]
POKEMONS_HOENN = ["Treecko", "Torchic", "Mudkip", "Ralts", "Kyogre", "Groudon", "Rayquaza"]


async def busca_pokemon_kanto():
    """Simula a busca de um Pokémon na região de Kanto."""
    print("🔍 Iniciando busca em Kanto...")
    
    # Simula o tempo de busca (1-5 segundos)
    tempo_busca = random.uniform(1, 5)
    await asyncio.sleep(tempo_busca)
    
    # Seleciona um Pokémon aleatório de Kanto
    pokemon_encontrado = random.choice(POKEMONS_KANTO)
    
    print(f"✅ Busca em Kanto concluída! (levou {tempo_busca:.2f}s)")
    return f"Kanto: {pokemon_encontrado}"


async def busca_pokemon_johto():
    """Simula a busca de um Pokémon na região de Johto."""
    print("🔍 Iniciando busca em Johto...")
    
    # Simula o tempo de busca (1-5 segundos)
    tempo_busca = random.uniform(1, 5)
    await asyncio.sleep(tempo_busca)
    
    # Seleciona um Pokémon aleatório de Johto
    pokemon_encontrado = random.choice(POKEMONS_JOHTO)
    
    print(f"✅ Busca em Johto concluída! (levou {tempo_busca:.2f}s)")
    return f"Johto: {pokemon_encontrado}"


async def busca_pokemon_hoenn():
    """Simula a busca de um Pokémon na região de Hoenn."""
    print("🔍 Iniciando busca em Hoenn...")
    
    # Simula o tempo de busca (1-5 segundos)
    tempo_busca = random.uniform(1, 5)
    await asyncio.sleep(tempo_busca)
    
    # Seleciona um Pokémon aleatório de Hoenn
    pokemon_encontrado = random.choice(POKEMONS_HOENN)
    
    print(f"✅ Busca em Hoenn concluída! (levou {tempo_busca:.2f}s)")
    return f"Hoenn: {pokemon_encontrado}"


async def main():
    """Função principal que coordena as buscas simultâneas."""
    print("=" * 60)
    print("🎮 SISTEMA DE BUSCA PARALELA DE POKÉMONS")
    print("=" * 60)
    print()
    
    # Marca o tempo inicial
    tempo_inicio = time.perf_counter()
    
    # Executa as três buscas simultaneamente usando asyncio.gather()
    resultados = await asyncio.gather(
        busca_pokemon_kanto(),
        busca_pokemon_johto(),
        busca_pokemon_hoenn()
    )
    
    # Marca o tempo final
    tempo_final = time.perf_counter()
    tempo_total = tempo_final - tempo_inicio
    
    # Exibe os resultados
    print()
    print("=" * 60)
    print("📊 RESULTADOS DA BUSCA")
    print("=" * 60)
    for resultado in resultados:
        print(f"  🎯 {resultado}")
    print()
    print(f"⏱️  Tempo total de execução: {tempo_total:.2f} segundos")
    print("=" * 60)
    print()
    print("💡 Nota: Se as buscas fossem sequenciais, levariam entre")
    print("   3 e 15 segundos. Com async, executamos todas simultaneamente!")


if __name__ == "__main__":
    # Executa a função principal
    asyncio.run(main())