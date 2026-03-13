files = [
    'templates/dashboard/projects/list.html',
    'templates/dashboard/roads/list.html',
    'templates/dashboard/org_units/list.html',
    'templates/dashboard/access/list.html'
]
for f in files:
    with open(f, 'r') as fp:
        s = fp.read()
    
    # Simple replace
    s = s.replace('          </button>\n        </button>\n      </div>\n    </div>\n  </div>', '          </button>\n        </button>\n      </div>\n    </form>\n  </div>')
    s = s.replace('          </button>\n      </div>\n    </div>\n  </div>', '          </button>\n      </div>\n    </form>\n  </div>')
    
    with open(f, 'w') as fp:
        fp.write(s)
