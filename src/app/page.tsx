'use client'

import { useState, useEffect, useCallback } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Skeleton } from '@/components/ui/skeleton'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { Loader2, Dice5, Sparkles, TrendingUp, AlertTriangle, Trophy, Brain, BarChart3, Target, Clock, Zap } from 'lucide-react'

type Lottery = {
  key: string
  name: string
  country: string
  main_pool_size: number
  main_picks: number
  bonus_pool_size: number
  bonus_picks: number
  draws_per_week: number
  currency: string
  min_jackpot: number
  odds_jackpot: number
  has_data: boolean
  data_path: string
}

type Engine = {
  key: string
  name: string
  description: string
}

type Prediction = {
  lottery: string
  engine: string
  prediction: number[]
  explanations?: Array<{
    rank: number
    number: number
    combined_score: number
    top_reasons: string[]
  }>
  last_draw?: {
    draw_number: number
    date: string
    main_numbers: number[]
  }
}

type LotteryInfo = {
  name: string
  country: string
  main_pool_size: number
  main_picks: number
  bonus_pool_size: number
  bonus_picks: number
  draws_per_week: number
  currency: string
  min_jackpot: number
  odds_jackpot: number
  total_draws: number
  date_range: [string, string] | null
  last_draw: { draw_number: number; date: string; main_numbers: number[] } | null
}

type BacktestComparison = {
  engine: string
  avg_hits: number
  max_hits: number
  avg_time_ms: number
  tested: number
}

type BacktestResult = {
  random_baseline: { avg_hits: number; max_hits: number; total_tested: number }
  comparison: BacktestComparison[]
}

export default function Home() {
  const [lotteries, setLotteries] = useState<Lottery[]>([])
  const [engines, setEngines] = useState<Engine[]>([])
  const [selectedLottery, setSelectedLottery] = useState<string>('')
  const [selectedEngine, setSelectedEngine] = useState<string>('ensemble')
  const [lotteryInfo, setLotteryInfo] = useState<LotteryInfo | null>(null)
  const [prediction, setPrediction] = useState<Prediction | null>(null)
  const [backtest, setBacktest] = useState<BacktestResult | null>(null)
  const [loadingPred, setLoadingPred] = useState(false)
  const [loadingInfo, setLoadingInfo] = useState(false)
  const [loadingBacktest, setLoadingBacktest] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Fetch lotteries and engines on mount
  useEffect(() => {
    Promise.all([
      fetch('/api/lotteries').then(r => r.json()),
      fetch('/api/engines').then(r => r.json()),
    ]).then(([lots, engs]: [Lottery[], Engine[]]) => {
      setLotteries(lots)
      setEngines(engs)
      const firstWithData = lots.find(l => l.has_data)
      if (firstWithData) {
        setSelectedLottery(firstWithData.key)
      }
    }).catch(e => setError(`Failed to load: ${e.message}`))
  }, [])

  // Fetch lottery info when selection changes
  useEffect(() => {
    if (!selectedLottery) return
    setLoadingInfo(true)
    setLotteryInfo(null)
    fetch(`/api/describe?lottery=${selectedLottery}`)
      .then(r => r.json())
      .then((data: LotteryInfo) => setLotteryInfo(data))
      .catch(e => setError(`Failed to load lottery info: ${e.message}`))
      .finally(() => setLoadingInfo(false))

    // Also fetch backtest
    setLoadingBacktest(true)
    setBacktest(null)
    fetch(`/api/backtest?lottery=${selectedLottery}`)
      .then(r => r.json())
      .then((data: BacktestResult) => {
        if (!data.error) setBacktest(data)
      })
      .catch(() => {})
      .finally(() => setLoadingBacktest(false))
  }, [selectedLottery])

  const handlePredict = useCallback(async () => {
    if (!selectedLottery || !selectedEngine) return
    setLoadingPred(true)
    setError(null)
    setPrediction(null)
    try {
      const res = await fetch(`/api/predict?lottery=${selectedLottery}&engine=${selectedEngine}`)
      const data: Prediction = await res.json()
      if ((data as any).error) {
        setError((data as any).error)
      } else {
        setPrediction(data)
      }
    } catch (e: any) {
      setError(`Prediction failed: ${e.message}`)
    } finally {
      setLoadingPred(false)
    }
  }, [selectedLottery, selectedEngine])

  const availableLotteries = lotteries.filter(l => l.has_data)
  const unavailableLotteries = lotteries.filter(l => !l.has_data)

  const formatOdds = (n: number) => {
    if (n >= 1_000_000) return `1 en ${n.toLocaleString('es-ES')}`
    return `1 en ${n.toLocaleString('es-ES')}`
  }

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-emerald-50 via-white to-emerald-50 dark:from-emerald-950/20 dark:via-background dark:to-emerald-950/20">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm dark:bg-background/80 sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-emerald-500 to-emerald-700 flex items-center justify-center">
              <Trophy className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight">LotteryPredictor</h1>
              <p className="text-xs text-muted-foreground">v2.0 · 10 motores · 18 loterías globales · 22K+ sorteos</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="hidden sm:inline-flex">
              <Brain className="w-3 h-3 mr-1" />
              LSTM + 9 estadísticos
            </Badge>
            <Badge variant="secondary" className="hidden sm:inline-flex">
              Backtested
            </Badge>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-6 flex-1">
        {error && (
          <Alert variant="destructive" className="mb-4">
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left column - Controls */}
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Target className="w-5 h-5 text-emerald-600" />
                  Configuración
                </CardTitle>
                <CardDescription>Selecciona lotería y motor</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Lotería</label>
                  <Select value={selectedLottery} onValueChange={setSelectedLottery}>
                    <SelectTrigger>
                      <SelectValue placeholder="Selecciona..." />
                    </SelectTrigger>
                    <SelectContent>
                      {availableLotteries.map(l => (
                        <SelectItem key={l.key} value={l.key}>
                          <div className="flex items-center gap-2">
                            <span>{l.name}</span>
                            <span className="text-xs text-muted-foreground">
                              ({l.main_picks}/{l.main_pool_size})
                            </span>
                          </div>
                        </SelectItem>
                      ))}
                      {unavailableLotteries.length > 0 && (
                        <>
                          <Separator className="my-1" />
                          <p className="px-2 py-1 text-xs text-muted-foreground">Sin datos:</p>
                          {unavailableLotteries.map(l => (
                            <SelectItem key={l.key} value={l.key} disabled>
                              {l.name} (sin datos)
                            </SelectItem>
                          ))}
                        </>
                      )}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Motor de predicción</label>
                  <Select value={selectedEngine} onValueChange={setSelectedEngine}>
                    <SelectTrigger>
                      <SelectValue placeholder="Selecciona..." />
                    </SelectTrigger>
                    <SelectContent>
                      {engines.map(e => (
                        <SelectItem key={e.key} value={e.key}>
                          <div className="flex flex-col">
                            <span>{e.name}</span>
                            <span className="text-xs text-muted-foreground">{e.description}</span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <Button
                  onClick={handlePredict}
                  disabled={loadingPred || !selectedLottery}
                  className="w-full bg-emerald-600 hover:bg-emerald-700"
                  size="lg"
                >
                  {loadingPred ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      {selectedEngine === 'lstm' ? 'Entrenando LSTM...' : 'Generando...'}
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4 mr-2" />
                      Generar Predicción
                    </>
                  )}
                </Button>
                {selectedEngine === 'lstm' && (
                  <p className="text-xs text-amber-600 flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    LSTM tarda ~15-30s en entrenar
                  </p>
                )}
              </CardContent>
            </Card>

            {/* Lottery info */}
            {loadingInfo ? (
              <Card>
                <CardContent className="p-4">
                  <Skeleton className="h-32 w-full" />
                </CardContent>
              </Card>
            ) : lotteryInfo ? (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">{lotteryInfo.name}</CardTitle>
                  <CardDescription>{lotteryInfo.country}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3 text-sm">
                  <div className="grid grid-cols-2 gap-2">
                    <InfoBox label="Formato" value={`${lotteryInfo.main_picks}/${lotteryInfo.main_pool_size}`} />
                    <InfoBox label="Sorteos/sem" value={String(lotteryInfo.draws_per_week)} />
                    <InfoBox label="Total sorteos" value={lotteryInfo.total_draws.toLocaleString()} />
                    <InfoBox label="Odds jackpot" value={`1:${lotteryInfo.odds_jackpot.toLocaleString()}`} />
                  </div>
                  {lotteryInfo.date_range && (
                    <div className="text-xs text-muted-foreground">
                      📅 {lotteryInfo.date_range[0]} → {lotteryInfo.date_range[1]}
                    </div>
                  )}
                  {lotteryInfo.last_draw && (
                    <div className="border-t pt-2">
                      <p className="text-xs text-muted-foreground mb-1">Último sorteo #{lotteryInfo.last_draw.draw_number}</p>
                      <div className="flex flex-wrap gap-1">
                        {lotteryInfo.last_draw.main_numbers.map((n, i) => (
                          <span key={i} className="w-7 h-7 rounded-full bg-emerald-100 text-emerald-700 dark:bg-emerald-900 dark:text-emerald-300 flex items-center justify-center text-xs font-bold">
                            {String(n).padStart(2, '0')}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            ) : null}
          </div>

          {/* Center column - Prediction */}
          <div className="lg:col-span-2 space-y-4">
            {/* Prediction result */}
            <Card className="border-emerald-200 dark:border-emerald-900">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Dice5 className="w-5 h-5 text-emerald-600" />
                  Predicción
                </CardTitle>
                <CardDescription>
                  {prediction
                    ? `Generada con ${prediction.engine} para ${prediction.lottery}`
                    : 'Selecciona lotería y motor, luego presiona Generar'}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {loadingPred ? (
                  <div className="space-y-3">
                    <Skeleton className="h-24 w-full" />
                    <Skeleton className="h-32 w-full" />
                  </div>
                ) : prediction ? (
                  <div className="space-y-4">
                    {/* Numbers display */}
                    <div className="flex flex-wrap justify-center gap-2 py-4">
                      {prediction.prediction.map((n, i) => (
                        <div
                          key={i}
                          className="w-14 h-14 rounded-full bg-gradient-to-br from-emerald-500 to-emerald-700 text-white flex items-center justify-center text-xl font-bold shadow-lg hover:scale-110 transition-transform"
                        >
                          {String(n).padStart(2, '0')}
                        </div>
                      ))}
                    </div>

                    {prediction.last_draw && (
                      <div className="text-center text-sm text-muted-foreground">
                        Último sorteo #{prediction.last_draw.draw_number} ({prediction.last_draw.date}):{' '}
                        <span className="font-mono">{prediction.last_draw.main_numbers.map(n => String(n).padStart(2, '0')).join(' ')}</span>
                      </div>
                    )}

                    {/* Explanations (only for ensemble) */}
                    {prediction.explanations && prediction.explanations.length > 0 && (
                      <div className="border-t pt-4">
                        <h3 className="text-sm font-semibold mb-2 flex items-center gap-2">
                          <Brain className="w-4 h-4" />
                          Justificación por número
                        </h3>
                        <ScrollArea className="h-[200px] rounded border p-2">
                          <Table>
                            <TableHeader>
                              <TableRow>
                                <TableHead className="w-12">#</TableHead>
                                <TableHead className="w-16">Número</TableHead>
                                <TableHead>Score</TableHead>
                                <TableHead>Motores que lo eligieron</TableHead>
                              </TableRow>
                            </TableHeader>
                            <TableBody>
                              {prediction.explanations.map(exp => (
                                <TableRow key={exp.rank}>
                                  <TableCell className="text-muted-foreground">{exp.rank}</TableCell>
                                  <TableCell>
                                    <span className="inline-flex w-8 h-8 rounded-full bg-emerald-100 dark:bg-emerald-900 text-emerald-700 dark:text-emerald-300 items-center justify-center font-bold text-xs">
                                      {String(exp.number).padStart(2, '0')}
                                    </span>
                                  </TableCell>
                                  <TableCell className="font-mono">{exp.combined_score.toFixed(3)}</TableCell>
                                  <TableCell className="text-xs">
                                    {exp.top_reasons.map((r, i) => (
                                      <div key={i} className="text-muted-foreground">{r}</div>
                                    ))}
                                  </TableCell>
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                        </ScrollArea>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
                    <Sparkles className="w-12 h-12 mb-3 opacity-30" />
                    <p className="text-sm">Presiona "Generar Predicción" para comenzar</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Backtest results */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <BarChart3 className="w-5 h-5 text-emerald-600" />
                  Backtest Comparativo
                </CardTitle>
                <CardDescription>
                  {backtest
                    ? `${backtest.comparison.length} motores vs azar · ${backtest.comparison[0]?.tested || 0} sorteos testeados`
                    : 'Validación histórica de cada motor'}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {loadingBacktest ? (
                  <Skeleton className="h-48 w-full" />
                ) : backtest ? (
                  <div className="space-y-2">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Motor</TableHead>
                          <TableHead className="text-right">Aciertos prom.</TableHead>
                          <TableHead className="text-right">Máx</TableHead>
                          <TableHead className="text-right">vs Azar</TableHead>
                          <TableHead className="text-right">Tiempo</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        <TableRow className="bg-muted/30">
                          <TableCell className="italic text-muted-foreground">🎲 Azar (baseline)</TableCell>
                          <TableCell className="text-right font-mono">{backtest.random_baseline.avg_hits.toFixed(3)}</TableCell>
                          <TableCell className="text-right">{backtest.random_baseline.max_hits}</TableCell>
                          <TableCell className="text-right text-muted-foreground">—</TableCell>
                          <TableCell className="text-right text-muted-foreground">—</TableCell>
                        </TableRow>
                        {backtest.comparison.map(c => {
                          const diff = c.avg_hits - backtest.random_baseline.avg_hits
                          const pct = (diff / backtest.random_baseline.avg_hits) * 100
                          return (
                            <TableRow key={c.engine}>
                              <TableCell className="font-medium">{c.engine}</TableCell>
                              <TableCell className="text-right font-mono">{c.avg_hits.toFixed(3)}</TableCell>
                              <TableCell className="text-right">{c.max_hits}</TableCell>
                              <TableCell className={`text-right font-mono ${diff > 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                                {diff > 0 ? '+' : ''}{diff.toFixed(3)} ({pct > 0 ? '+' : ''}{pct.toFixed(1)}%)
                              </TableCell>
                              <TableCell className="text-right text-xs text-muted-foreground">{c.avg_time_ms.toFixed(1)}ms</TableCell>
                            </TableRow>
                          )
                        })}
                      </TableBody>
                    </Table>
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground text-center py-8">
                    No hay backtest disponible para esta lotería
                  </p>
                )}
              </CardContent>
            </Card>

            {/* Disclaimer */}
            <Alert>
              <AlertTriangle className="h-4 w-4" />
              <AlertTitle>Aviso importante</AlertTitle>
              <AlertDescription className="text-xs">
                La lotería es esencialmente aleatoria. El backtesting muestra que ningún motor supera
                significativamente al azar (mejoras marginales &lt;5%). Juega con responsabilidad,
                solo dinero que puedas permitirte perder. Esta herramienta es para fines educativos
                y de análisis estadístico, no garantiza ganancias.
              </AlertDescription>
            </Alert>
          </div>
        </div>

        {/* Tabs section with more info */}
        <Tabs defaultValue="architecture" className="mt-6">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="architecture">Arquitectura</TabsTrigger>
            <TabsTrigger value="engines">Motores</TabsTrigger>
            <TabsTrigger value="lotteries">Loterías</TabsTrigger>
          </TabsList>
          <TabsContent value="architecture">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Arquitectura del sistema</CardTitle>
              </CardHeader>
              <CardContent className="text-sm space-y-2">
                <p><strong>Sistema modular</strong> con 10 motores de análisis independientes + ensemble combinado.</p>
                <p><strong>Multi-lotería</strong>: 6 loterías globales configurables (Pozo Millonario, La Primitiva, EuroMillions, EuroJackpot, El Gordo, Lotto austriaco).</p>
                <p><strong>Stack:</strong> Python 3.12 stdlib + TensorFlow 2.21 (para LSTM) + Next.js 16 + TypeScript.</p>
                <p><strong>Backtesting incluido</strong>: validación histórica de cada motor contra datos reales.</p>
                <p><strong>Fuentes de datos:</strong></p>
                <ul className="list-disc pl-5 space-y-1 text-xs">
                  <li>Pozo Millonario: scrapeado de pozomillonario.info (308 sorteos, 2021-2026)</li>
                  <li>EuroMillions: GitHub daowa89/lottery-archive (1977 sorteos, 2004-2026)</li>
                  <li>La Primitiva: proxy con Lotto 6aus49 alemán (5049 sorteos, 1955-2026, mismo formato 6/49)</li>
                  <li>Lotto austriaco: GitHub daowa89/lottery-archive (3684 sorteos, 1986-2026)</li>
                </ul>
              </CardContent>
            </Card>
          </TabsContent>
          <TabsContent value="engines">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">10 motores de análisis</CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>#</TableHead>
                      <TableHead>Motor</TableHead>
                      <TableHead>Descripción</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {engines.map((e, i) => (
                      <TableRow key={e.key}>
                        <TableCell>{i + 1}</TableCell>
                        <TableCell className="font-medium">{e.name}</TableCell>
                        <TableCell className="text-xs text-muted-foreground">{e.description}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>
          <TabsContent value="lotteries">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Loterías soportadas</CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Lotería</TableHead>
                      <TableHead>País</TableHead>
                      <TableHead>Formato</TableHead>
                      <TableHead>Odds</TableHead>
                      <TableHead>Estado</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {lotteries.map(l => (
                      <TableRow key={l.key}>
                        <TableCell className="font-medium">{l.name}</TableCell>
                        <TableCell>{l.country}</TableCell>
                        <TableCell>{l.main_picks}/{l.main_pool_size}{l.bonus_picks ? ` + ${l.bonus_picks}/${l.bonus_pool_size}` : ''}</TableCell>
                        <TableCell className="text-xs font-mono">1:{l.odds_jackpot.toLocaleString()}</TableCell>
                        <TableCell>
                          {l.has_data ? (
                            <Badge variant="default" className="bg-emerald-600">✓ Listo</Badge>
                          ) : (
                            <Badge variant="outline">Sin datos</Badge>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>

      <footer className="border-t bg-muted/30 mt-auto">
        <div className="container mx-auto px-4 py-4 text-center text-xs text-muted-foreground">
          <p>LotteryPredictor v1.0 · 10 motores · 6 loterías · Backtested · TensorFlow LSTM</p>
          <p className="mt-1">⚠️ Juega con responsabilidad. La lotería NO es inversión.</p>
        </div>
      </footer>
    </div>
  )
}

function InfoBox({ label, value }: { label: string; value: string }) {
  return (
    <div className="border rounded p-2">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="font-semibold text-sm">{value}</div>
    </div>
  )
}
