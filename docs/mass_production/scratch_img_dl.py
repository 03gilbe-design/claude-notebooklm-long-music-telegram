import base64

svg_audio = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 300">
  <rect width="300" height="300" rx="60" fill="#8B5CF6" />
  <path d="M150 70 L150 230 M100 120 L100 180 M200 100 L200 200 M50 140 L50 160 M250 130 L250 170" stroke="#FFF" stroke-width="20" stroke-linecap="round" />
</svg>'''
b64_audio = base64.b64encode(svg_audio.encode('utf-8')).decode('utf-8')
print('EP_IMG=data:image/svg+xml;base64,' + b64_audio)
