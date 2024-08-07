from loguru import logger
import random
import subprocess
import time
from lib.messages import (
    WAITING_MESSAGE,
    ACTIONS_AFTER_END_GAME_MESSAGE,
    LOBBY_DETECTED_MESSAGE,
    CANNOT_FIND_BATTLE_BUTTON_MESSAGE,
    NEW_SCREEN_STATE_MESSAGE,
    MAIN_MENU_MESSAGE,
    NO_ACTIONS_AVAILABLE_MESSAGE,
    THANK_YOU_MESSAGE
)

from clashroyalebuildabot.bot import Bot
from clashroyalebuildabot.bot.example.custom_action import CustomAction
from clashroyalebuildabot.namespaces.cards import Cards
from clashroyalebuildabot.namespaces.screens import Screens

class CustomBot(Bot):
    PRESET_DECK = [
        Cards.MINIONS,
        Cards.ARCHERS,
        Cards.ARROWS,
        Cards.GIANT,
        Cards.MINIPEKKA,
        Cards.FIREBALL,
        Cards.KNIGHT,
        Cards.MUSKETEER,
    ]

    def __init__(self, cards=None, debug=False):
        if cards is not None:
            raise ValueError(
                f"CustomBot uses a preset deck: {self.PRESET_DECK}."
                "Use cards=None instead."
            )
        super().__init__(self.PRESET_DECK, CustomAction, debug=debug)
        self.end_of_game_clicked = False
        self.pause_until = 0

    def _restart_game(self):
        subprocess.run(
            "adb shell am force-stop com.supercell.clashroyale", shell=True
        )
        time.sleep(1)
        subprocess.run(
            "adb shell am start -n com.supercell.clashroyale/com.supercell.titan.GameApp",
            shell=True,
        )
        logger.info(WAITING_MESSAGE)
        time.sleep(10)
        self.end_of_game_clicked = False

    def _end_of_game(self):
        if time.time() < self.pause_until:
            time.sleep(1)
            return

        self.set_state()
        actions = self.get_actions()
        logger.info(ACTIONS_AFTER_END_GAME_MESSAGE.format(actions=actions))

        if self.state.screen == Screens.LOBBY:
            logger.debug(LOBBY_DETECTED_MESSAGE)
            return

        logger.info(CANNOT_FIND_BATTLE_BUTTON_MESSAGE)
        self._restart_game()

    def step(self):
        if self.end_of_game_clicked:
            self._end_of_game()
            return

        old_screen = self.state.screen if self.state else None
        self.set_state()
        new_screen = self.state.screen
        if new_screen != old_screen:
            logger.info(NEW_SCREEN_STATE_MESSAGE.format(new_screen=new_screen))

        if new_screen == "end_of_game":
            logger.info("End of game detected. Waiting 10 seconds for battle button")
            self.pause_until = time.time() + 10
            self.end_of_game_clicked = True
            time.sleep(10)
            return

        if new_screen == "lobby":
            logger.info(MAIN_MENU_MESSAGE)
            time.sleep(1)
            return

        actions = self.get_actions()
        if not actions:
            logger.debug(NO_ACTIONS_AVAILABLE_MESSAGE)
            time.sleep(1)
            return

        random.shuffle(actions)
        action = max(actions, key=lambda x: x.calculate_score(self.state))
        if action.score[0] == 0:
            time.sleep(1)
            return

        self.play_action(action)
        logger.info(f"Playing {action} with score {action.score}. Waiting for 1 second")
        time.sleep(1)

    def run(self):
        try:
            while True:
                self.step()
        except KeyboardInterrupt:
            logger.info(THANK_YOU_MESSAGE)

if __name__ == "__main__":
    bot = CustomBot(debug=True)
    bot.run()
