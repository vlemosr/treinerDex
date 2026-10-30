from bisect import bisect_right


RAW_LEVEL_XP = """
1 0
2 98
3 199
4 388
5 790
6 1.498
7 2.565
8 4.176
9 6.397
10 9.230
11 12.956
12 17.596
13 23.083
14 29.830
15 37.795
16 46.824
17 57.489
18 69.694
19 83.153
20 96.660
21 115.993
22 134.770
23 156.016
24 179.392
25 204.375
26 232.266
27 262.591
28 294.668
29 330.110
30 368.290
31 408.349
32 452.248
33 499.189
34 548.118
35 601.380
36 657.988
37 716.675
38 780.206
39 847.387
40 916.720
41 991.426
42 1.070.086
43 1.150.953
44 1.237.740
45 1.328.785
46 1.422.074
47 1.521.848
48 1.626.184
49 1.732.783
50 1.846.450
51 1.964.983
52 2.085.780
53 2.214.246
54 2.347.882
55 2.483.765
56 2.627.936
57 2.777.581
58 2.929.438
59 3.090.220
60 3.256.780
61 3.425.499
62 3.603.798
63 3.788.179
64 3.974.648
65 4.171.370
66 4.374.478
67 4.579.585
68 4.795.636
69 5.018.377
70 5.243.010
71 5.479.296
72 5.722.576
73 5.967.623
74 6.225.050
75 6.489.775
76 6.756.124
77 7.035.598
78 7.322.674
79 7.611.213
80 7.913.640
81 8.223.973
82 8.535.590
83 8.861.876
84 9.196.372
85 9.531.955
86 9.883.006
87 10.242.571
88 10.603.008
89 10.979.730
90 11.365.270
91 11.751.449
92 12.154.748
93 12.567.169
94 12.979.978
95 13.410.760
96 13.850.968
97 14.291.295
98 14.750.466
99 15.219.367
100 15.688.100
101 16.176.566
102 16.675.066
103 17.173.093
104 17.691.760
105 18.220.765
106 18.748.974
107 19.298.748
108 19.859.164
109 20.418.443
110 21.000.230
111 21.592.963
112 22.184.200
113 22.798.906
114 23.424.862
115 24.048.945
116 24.697.476
117 25.357.561
118 26.015.378
119 26.698.640
120 27.393.760
121 28.086.199
122 28.805.098
123 29.536.159
124 30.264.108
125 31.019.550
126 31.787.458
127 32.551.805
128 33.344.696
129 34.150.357
130 34.951.990
131 35.783.236
132 36.627.556
133 37.467.363
134 38.337.870
135 39.221.755
136 40.100.624
137 41.011.298
138 41.935.654
139 42.854.473
140 43.806.220
141 44.771.953
142 45.731.610
143 46.725.336
144 47.733.352
145 48.734.735
146 49.771.346
147 50.822.551
148 51.866.548
149 52.946.950
150 54.042.250
151 55.129.749
152 56.254.848
153 57.395.149
154 58.527.038
155 59.697.740
156 60.883.948
157 62.061.115
158 63.278.326
159 64.511.347
160 65.734.680
161 66.999.306
162 68.280.046
163 69.550.433
164 70.863.380
165 72.192.745
166 73.511.074
167 74.873.248
168 76.252.144
169 77.619.303
170 79.031.610
171 80.460.943
172 81.877.820
173 83.341.166
174 84.821.842
175 86.289.325
176 87.804.616
177 89.337.541
178 90.856.518
179 92.424.660
180 94.010.740
181 95.582.099
182 97.203.998
183 98.844.139
184 100.468.768
185 102.145.330
186 103.840.438
187 105.519.225
188 107.251.356
189 109.002.337
190 110.736.170
191 112.524.776
192 114.332.536
193 116.122.303
194 117.968.290
195 119.833.735
196 121.680.324
197 123.584.598
198 125.500.634
199 127.412.933
200 129.376.400
201 131.359.933
202 133.322.830
203 135.346.396
204 137.390.332
205 139.412.715
206 141.497.286
207 143.602.531
208 145.685.288
209 147.831.770
210 149.999.230
211 152.143.249
212 154.352.548
213 156.583.129
214 158.789.298
215 161.062.320
216 163.356.928
217 165.626.135
218 167.963.786
219 170.323.327
220 172.656.460
221 175.059.646
222 177.485.026
223 179.882.973
224 182.352.600
225 184.844.725
226 187.308.374
227 189.845.348
228 192.405.124
229 194.935.363
230 197.540.590
231 200.168.923
232 202.766.640
233 205.441.026
234 208.138.822
235 210.804.905
236 213.549.356
237 216.317.521
238 219.052.858
239 221.868.280
240 224.707.720
241 227.531.199
242 230.400.498
243 233.312.119
244 236.188.628
245 239.148.710
246 242.133.418
247 245.081.845
248 248.115.616
249 251.174.317
250 254.195.550
251 257.303.916
252 260.437.516
253 263.532.443
254 266.716.310
255 269.925.715
256 273.095.224
257 276.355.498
258 279.641.614
259 282.886.593
260 286.224.180
261 289.587.913
262 292.909.250
263 296.325.056
264 299.767.312
265 303.165.895
266 306.660.826
267 310.182.511
268 313.659.228
269 317.234.190
270 320.836.210
271 324.391.949
272 328.047.848
273 331.731.109
274 335.366.758
275 339.104.500
276 342.869.908
277 346.586.355
278 350.406.846
279 354.255.307
280 358.053.440
281 361.957.586
282 365.890.006
283 369.770.713
284 373.759.420
285 377.776.705
286 381.740.874
287 385.815.048
288 389.918.104
289 393.966.623
290 398.127.170
291 402.316.903
292 406.450.660
293 410.698.486
294 414.975.802
295 419.195.685
296 423.531.696
297 427.897.501
298 432.204.398
299 436.629.500
300 441.084.700
"""


LEVEL_TOTAL_XP = {
    int(level): int(total_xp.replace('.', ''))
    for level, total_xp in (line.split() for line in RAW_LEVEL_XP.strip().splitlines())
}
LEVELS = sorted(LEVEL_TOTAL_XP)
TOTAL_XP_BY_LEVEL = [LEVEL_TOTAL_XP[level] for level in LEVELS]
MIN_LEVEL = LEVELS[0]
MAX_LEVEL = LEVELS[-1]
BASE_HP = 100
REFERENCE_HP_LEVEL = 333
REFERENCE_MAX_HP = 5100


def get_max_hp_for_level(level):
    """Return HP on a linear curve from level 1 to the configured reference."""
    level = max(1, int(level))
    level_steps = REFERENCE_HP_LEVEL - 1
    hp_gain = REFERENCE_MAX_HP - BASE_HP
    # Integer half-up rounding keeps the result deterministic without floats.
    return BASE_HP + ((hp_gain * (level - 1) + level_steps // 2) // level_steps)


def get_total_xp_for_level(level):
    level = int(level)
    if level not in LEVEL_TOTAL_XP:
        raise ValueError(f'Nivel fora da tabela de experiencia: {level}')
    return LEVEL_TOTAL_XP[level]


def get_level_for_total_xp(total_xp):
    total_xp = max(0, int(total_xp))
    index = bisect_right(TOTAL_XP_BY_LEVEL, total_xp) - 1
    return LEVELS[max(0, index)]


def get_level_progress(total_xp):
    total_xp = max(0, int(total_xp))
    level = get_level_for_total_xp(total_xp)
    level_start_xp = get_total_xp_for_level(level)

    if level >= MAX_LEVEL:
        return {
            'level': MAX_LEVEL,
            'total_xp': total_xp,
            'level_start_xp': level_start_xp,
            'next_level': None,
            'next_level_xp': level_start_xp,
            'gained_this_level': 0,
            'needed_for_next_level': 0,
            'percent': 100,
            'percent_css': '100',
        }

    next_level = level + 1
    next_level_xp = get_total_xp_for_level(next_level)
    needed_for_next_level = next_level_xp - level_start_xp
    gained_this_level = min(total_xp - level_start_xp, needed_for_next_level)
    percent = round((gained_this_level / needed_for_next_level) * 100, 2)

    return {
        'level': level,
        'total_xp': total_xp,
        'level_start_xp': level_start_xp,
        'next_level': next_level,
        'next_level_xp': next_level_xp,
        'gained_this_level': gained_this_level,
        'needed_for_next_level': needed_for_next_level,
        'percent': percent,
        'percent_css': f'{percent:.2f}',
    }


def sync_trainer_experience(trainer, save=True):
    progress = get_level_progress(trainer.current_xp)
    trainer.level = progress['level']
    trainer.next_level_xp = progress['next_level_xp']
    previous_max_hp = trainer.max_hp
    trainer.max_hp = get_max_hp_for_level(trainer.level)
    trainer.current_hp = min(
        trainer.max_hp,
        max(0, trainer.current_hp + trainer.max_hp - previous_max_hp),
    )
    if save:
        trainer.save(update_fields=[
            'level',
            'next_level_xp',
            'current_hp',
            'max_hp',
            'updated_at',
        ])
    return progress


def add_trainer_xp(trainer, amount):
    amount = int(amount)
    if amount < 0:
        raise ValueError('A quantidade de XP nao pode ser negativa.')

    trainer.current_xp += amount
    progress = sync_trainer_experience(trainer, save=False)
    trainer.save(update_fields=[
        'level',
        'current_xp',
        'next_level_xp',
        'current_hp',
        'max_hp',
        'updated_at',
    ])
    return progress
