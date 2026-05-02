import sys
import pygame
from src.game import Game


def main():
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("GrimDeck – Dungeon Crawler")
    clock = pygame.time.Clock()

    game = Game(screen)

    while True:
        events = pygame.event.get()
        for ev in events:
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        game.update(events)
        game.render()
        clock.tick(60)


if __name__ == "__main__":
    main()
