class AlienGame {
    constructor() {
        this.currentLevel = 0;
        this.doorAreas = [];
        this.currentLevelIsDark = false;
        this.alienChance = 0;
        this.apiBaseUrl = '/api';
        this.lastDoorsCount = 0;
        this.flashlight = $('#flashlight');
        this.isFlashlightActive = true;
        this.sessionId = null;
        
        this.initializeEventListeners();
        this.setupFlashlight();
        this.initializeSession();
    }

    async initializeSession() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/game/status`, {
                credentials: 'include'
            });
            
            if (response.ok) {
                const status = await response.json();
                this.currentLevel = status.current_level;
                this.alienChance = status.alien_chance;
                
                if (this.currentLevel > 0) {
                    this.showScreen('game-screen');
                    this.hideScreen('start-screen');
                    await this.loadLevel(this.currentLevel);
                }
            }
        } catch (error) {
            console.log('Новая сессия будет создана при старте игры');
        }
    }

    setupFlashlight() {
        const overlay = $('#dark-overlay');
        overlay.addClass('flashlight-active');
        
        $(document).on('mousemove', (e) => {
            if (this.isFlashlightActive && $('#game-screen').hasClass('visible')) {
                overlay.css({
                    '--mouse-x': e.pageX + 'px',
                    '--mouse-y': e.pageY + 'px'
                });
            }
        });
    }
    
    initializeEventListeners() {
        $('#start-btn').on('click', () => {
            this.startGame();
        });
        
        $('.restart-btn').on('click', () => {
            this.restartGame();
        });
        
        $(window).on('resize', () => this.handleResize());
    }
    
    handleResize() {
        if (this.currentLevel > 0 && this.lastDoorsCount > 0) {
            this.createDoorAreas(this.lastDoorsCount);
        }
    }
    
    async startGame() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/game/start`);
            if (!response.ok) throw new Error('Network error');
            
            const data = await response.json();
            
            if (data.message === 'Game started') {
                this.showScreen('game-screen');
                this.hideScreen('start-screen');
                this.currentLevel = 1;
                this.alienChance = 0;
                await this.loadLevel(this.currentLevel);
            }
        } catch (error) {
            console.error('Ошибка при запуске игры:', error);
        }
    }
    
    async loadLevel(levelNumber) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/game/level/${levelNumber}`);
            if (!response.ok) throw new Error('Level load error');
            
            const levelData = await response.json();
            
            $('#level-image').attr('src', `${this.apiBaseUrl}/images/${levelData.doors_count}.png`);

            $('#runner').addClass('hidden');
            this.lastDoorsCount = levelData.doors_count;
            this.createDoorAreas(levelData.doors_count);
            
            if (levelData.has_runner) {
                this.showRunner();
            }
            
            if (levelData.is_dark) {
                $('#dark-overlay').removeClass('hidden');
                this.flashlight.addClass('visible');
                this.isFlashlightActive = true;
            } else {
                $('#dark-overlay').addClass('hidden');
                this.flashlight.removeClass('visible');
                this.isFlashlightActive = false;
            }
            
        } catch (error) {
            console.error('Ошибка при загрузке уровня:', error);
        }
    }

    showScreen(screenId) {
        $('.screen').removeClass('visible');
        $(`#${screenId}`).addClass('visible');
        
        if (screenId === 'game-screen') {
            if (this.currentLevelIsDark) {
                $('#dark-overlay').removeClass('hidden');
                this.flashlight.addClass('visible');
                this.isFlashlightActive = true;
            } else {
                $('#dark-overlay').addClass('hidden');
                this.flashlight.removeClass('visible');
                this.isFlashlightActive = false;
            }
        } else {
            $('#dark-overlay').addClass('hidden');
            this.flashlight.removeClass('visible');
            this.isFlashlightActive = false;
        }
    }
    
    createDoorAreas(doorsCount) {
        const container = $('#doors-container');
        container.empty();
        this.doorAreas = [];
        
        const positions = this.calculateDoorPositions(doorsCount);
        
        for (let i = 0; i < doorsCount; i++) {
            const doorArea = $('<div>').addClass('door-area').attr('data-door', i + 1);
            doorArea.css({
                width: `${positions[i].width}px`,
                height: `${positions[i].height}px`,
                left: `${positions[i].x}px`,
                top: `${positions[i].y}px`
            });
            
            const highlight = $('<div>').addClass('door-highlight');
            doorArea.append(highlight);
            
            doorArea.on('click', (e) => {
                e.stopPropagation();
                this.selectDoor(i + 1);
            });
            
            doorArea.on('mouseenter', () => {
                highlight.css({
                    opacity: 1,
                    boxShadow: '0 0 20px #00ff00, inset 0 0 10px #00ff00'
                });
            });
            
            doorArea.on('mouseleave', () => {
                highlight.css({
                    opacity: 0,
                    boxShadow: 'none'
                });
            });
            
            container.append(doorArea);
            this.doorAreas.push(doorArea);
        }
    }
    
    calculateDoorPositions(doorsCount) {
        const positions = [];
        const screenWidth = $(window).width();
        const screenHeight = $(window).height();
        
        switch (doorsCount) {
            case 1:
                positions.push({ 
                    x: 1000,
                    y: 230,
                    width: 620,
                    height: 620
                });
                break;
            case 2:
                positions.push({ 
                    x: 200,
                    y: 400,
                    width: 450,
                    height: 450
                });
                positions.push({ 
                    x: 1150,
                    y: 400,
                    width: 450,
                    height: 450
                });
                break;
            case 3:
                positions.push({ 
                    x: 150,
                    y: 240,
                    width: 380,
                    height: 380
                });
                positions.push({ 
                    x: 725,
                    y: 240,
                    width: 380,
                    height: 380
                });
                positions.push({ 
                    x: 1300,
                    y: 240,
                    width: 380,
                    height: 380
                });
                break;
            case 4:
                positions.push({ 
                    x: 40,
                    y: 490,
                    width: 350,
                    height: 350
                });
                positions.push({ 
                    x: 440,
                    y: 490,
                    width: 350,
                    height: 350
                });
                positions.push({ 
                    x: 1030,
                    y: 490,
                    width: 350,
                    height: 350
                });
                positions.push({ 
                    x: 1430,
                    y: 490,
                    width: 350,
                    height: 350
                });
                break;
            case 5:
                positions.push({ 
                    x: 90,
                    y: 650,
                    width: 250,
                    height: 250
                });
                positions.push({ 
                    x: 410,
                    y: 650,
                    width: 250,
                    height: 250
                });
                positions.push({ 
                    x: 750,
                    y: 600,
                    width: 350,
                    height: 350
                });
                positions.push({ 
                    x: 1160,
                    y: 650,
                    width: 250,
                    height: 250
                });
                positions.push({ 
                    x: 1480,
                    y: 650,
                    width: 250,
                    height: 250
                });
                break;
        }
        
        return positions;
    }
    
    async selectDoor(doorNumber) {
        try {
            this.doorAreas.forEach(door => door.css('pointer-events', 'none'));
            
            const response = await fetch(`${this.apiBaseUrl}/game/select_door/${this.currentLevel}/${doorNumber}`, {
                method: 'POST',
                credentials: 'include'
            });
            
            if (!response.ok) throw new Error('Door selection error');
            
            const result = await response.json();
            this.currentLevel++;
            this.alienChance = result.alien_chance || 0;
            
            if (result.alien_encounter) {
                this.showAlienEncounter();
                return;
            }
            
            if (result.game_completed) {
                this.showWinScreen(result.flag);
            } else {
                await this.loadLevel(this.currentLevel);
            }
            
        } catch (error) {
            console.error('Ошибка при выборе двери:', error);
        } finally {
            this.doorAreas.forEach(door => door.css('pointer-events', 'auto'));
        }
    }
    
    showRunner() {
        $('#runner').removeClass('hidden').css('animation', 'none');
        setTimeout(() => $('#runner').css('animation', 'runAcross 1s linear'), 10);
        setTimeout(() => $('#runner').addClass('hidden'), 1000);
    }
    
    showAlienEncounter() {
        this.showScreen('alien-screen');
    }
    
    showWinScreen(flag) {
        console.log(flag);
        document.getElementById('flag').innerText = flag;
        $('#flag').innerText = flag;
        this.showScreen('win-screen');
    }
    
    showScreen(screenId) {
        $('.screen').removeClass('visible');
        $(`#${screenId}`).addClass('visible');
    }
    
    hideScreen(screenId) {
        $(`#${screenId}`).removeClass('visible');
    }
    
    restartGame() {
        this.showScreen('start-screen');
        $('.screen').not('#start-screen').removeClass('visible');
        this.currentLevel = 0;
        this.alienChance = 0;
        this.doorAreas = [];
        this.currentLevelIsDark = false;
        $('#doors-container').empty();
        $('#dark-overlay').addClass('hidden');
        this.flashlight.removeClass('visible');
        this.isFlashlightActive = false;
    }
}

$(document).ready(() => {
    window.game = new AlienGame();
});