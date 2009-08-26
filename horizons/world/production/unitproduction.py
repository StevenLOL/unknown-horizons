# -*- coding: utf-8 -*-
# ###################################################
# Copyright (C) 2009 The Unknown Horizons Team
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

from horizons.world.production.production import SingleUseProgressProduction

class UnitProduction(SingleUseProgressProduction):
	"""Production, that produces units."""
	def __init__(self, **kwargs):
		super(UnitProduction, self).__init__(**kwargs)


	def _give_produced_res(self):
		"""This needs to be overridden as we also have to produce the unit."""
		super(UnitProduction, self)._give_produced_res()
		self.__create_unit()

	def __create_unit(self):
		"""Private function that creates a unit in the home_buildings radius."""
