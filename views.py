import os
import sys

from main import app

from flask import render_template, flash


def home():
    """Render the home page."""
    return render_template('home.html')

def contacts():
    """Render the contacts page."""
    return render_template('contacts.html')

def help():
    """Render the help page."""
    return render_template('help.html')

def downloads():
    """Render the downloads page."""
    return render_template('downloads.html')

def culling():
    """Render the culling entry page."""
    flash('Post saved on database.')
    return render_template('culling.html', speciesTextBox='', pc=20, minRes=0.0, maxRes=3.0, maxRVal=0.5, minLen=40, maxLen=10000, enforceMinLength=False,
		enforceMaxLength=False, includeNonXray=False, includeAlphaCarbon=False, cullByEntry=False, intraEntryCull=False, intraEntryPC=20)