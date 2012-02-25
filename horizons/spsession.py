# ###################################################
# Copyright (C) 2012 The Unknown Horizons Team
# team@unknown-horizons.org
# This file is part of Unknown Horizons.
#
# Unknown Horizons is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the
# Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# ###################################################

import random
import os
import time
import traceback
import json

import horizons.main

from horizons.session import Session
from horizons.manager import SPManager
from horizons.extscheduler import ExtScheduler
from horizons.constants import GAME_SPEED, SINGLEPLAYER
from horizons.savegamemanager import SavegameManager
from horizons.util.dbreader import DbReader
from horizons.timer import Timer
from horizons.util.uhdbaccessor import read_savegame_template


class SPSession(Session):
	"""Session tailored for singleplayer games."""

	def create_manager(self):
		return SPManager(self)

	def create_rng(self, seed=None):
		return random.Random(seed if seed is not None else SINGLEPLAYER.SEED)

	def create_timer(self):
		return Timer(freeze_protection=True)

	def load(self, *args, **kwargs):
		super(SPSession, self).load(*args, **kwargs)
		# single player games start right away
		self.start()

	def speed_set(self, ticks, suggestion=False):
		"""Set game speed to ticks ticks per second"""
		old = self.timer.ticks_per_second
		self.timer.ticks_per_second = ticks
		self.view.map.setTimeMultiplier(float(ticks) / float(GAME_SPEED.TICKS_PER_SECOND))
		if old == 0 and self.timer.tick_next_time is None: #back from paused state
			if self.paused_time_missing is None:
				# happens if e.g. a dialog pauses the game during startup on hotkeypress
				self.timer.tick_next_time = time.time()
			else:
				self.timer.tick_next_time = time.time() + (self.paused_time_missing / ticks)
		elif ticks == 0 or self.timer.tick_next_time is None:
			# go into paused state or very early speed change (before any tick)
			if self.timer.tick_next_time is not None:
				self.paused_time_missing = (self.timer.tick_next_time - time.time()) * old
			else:
				self.paused_time_missing =  None
			self.timer.tick_next_time = None
		else:
			"""
			Under odd circumstances (anti-freeze protection just activated, game speed
			decremented multiple times within this frame) this can delay the next tick
			by minutes. Since the positive effects of the code aren't really observeable,
			this code is commented out and possibly will be removed.

			# correct the time until the next tick starts
			time_to_next_tick = self.timer.tick_next_time - time.time()
			if time_to_next_tick > 0: # only do this if we aren't late
				self.timer.tick_next_time += (time_to_next_tick * old / ticks)
			"""
		self.display_speed()

	def autosave(self):
		"""Called automatically in an interval"""
		self.log.debug("Session: autosaving")
		success = self._do_save(SavegameManager.create_autosave_filename())
		if success:
			SavegameManager.delete_dispensable_savegames(autosaves = True)
			self.ingame_gui.message_widget.add(None, None, 'AUTOSAVE')

	def quicksave(self):
		"""Called when user presses the quicksave hotkey"""
		self.log.debug("Session: quicksaving")
		# call saving through horizons.main and not directly through session, so that save errors are handled
		success = self._do_save(SavegameManager.create_quicksave_filename())
		if success:
			SavegameManager.delete_dispensable_savegames(quicksaves = True)
			self.ingame_gui.message_widget.add(None, None, 'QUICKSAVE')
		else:
			headline = _(u"Failed to quicksave.")
			descr = _(u"An error happened during quicksave. Your game has not been saved.")
			advice = _(u"If this error happens again, please contact the development team:") + \
			           u"unknown-horizons.org/support/"
			self.gui.show_error_popup(headline, descr, advice)

	def quickload(self):
		"""Loads last quicksave"""
		files = SavegameManager.get_quicksaves(include_displaynames = False)[0]
		if len(files) == 0:
			self.gui.show_popup(_("No quicksaves found"), _("You need to quicksave before you can quickload."))
			return
		self.ingame_gui.on_escape() # close widgets that might be open
		horizons.main.load_game(savegame=files[0])

	def save(self, savegamename=None):
		"""Saves a game
		@param savegamename: string with the full path of the savegame file or None to let user pick one
		@return: bool, whether no error happened (user aborting dialog means success)
		"""
		if savegamename is None:
			savegamename = self.gui.show_select_savegame(mode='save')
			if savegamename is None:
				return True # user aborted dialog
			savegamename = SavegameManager.create_filename(savegamename)

		success= self._do_save(savegamename)
		if success:
			self.ingame_gui.message_widget.add(None, None, 'SAVED_GAME')
		return success
