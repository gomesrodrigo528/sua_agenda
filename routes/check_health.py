from flask import Flask, Blueprint, render_template, request, redirect, url_for
from flask import flash, session
from flask import current_app as app
from supabase import create_client, Client
import os
import datetime



check_health_bp = Blueprint('check_health_bp', __name__)


@check_health_bp.route('/check_health', methods=['GET'])
def check_base():
    return render_template('base.html')