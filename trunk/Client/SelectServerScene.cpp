#include "Game.h"

SelectServerScene::SelectServerScene()
{
	SelectServerFocus = Abaddon;
}

void SelectServerScene::Draw(SDL_Surface *Dest)
{
	Sprite::Draw(Dest, Game::GetInstance().Sprites[SPRID_LOGIN], 0, 0, SPRID_LOGIN_BACKGROUND);
	Sprite::Draw(Dest, Game::GetInstance().Sprites[SPRID_LOGIN], 40, 121, SPRID_SELECTSERVER_FRAME);

	switch(SelectServerFocus)
	{
	case Abaddon:
		Sprite::Draw(Dest, Game::GetInstance().Sprites[SPRID_LOGIN], 139, 176, SPRID_SELECTSERVER_BUTTON_ABADDON);
		break;
	case Apocalypse:
		Sprite::Draw(Dest, Game::GetInstance().Sprites[SPRID_LOGIN], 131, 204, SPRID_SELECTSERVER_BUTTON_APOCALYPSE);
		break;
	case Cancel:
		Sprite::Draw(Dest, Game::GetInstance().Sprites[SPRID_LOGIN], 257, 282, SPRID_LOGIN_BUTTON_CANCEL);
		break;
	}
}

void SelectServerScene::OnMouseMove(int X, int Y, int RelX, int RelY, bool Left, bool Right, bool Middle)
{
	if(X > 139 && X < (139+138)) // Abaddon Button
	{
		if(Y > 176 && Y < (176+19))
		{
			SelectServerFocus = Abaddon;
		}
	}

	if(X > 131 && X < (139+157)) // Apocalypse Button
	{
		if(Y > 204 && Y < (204+19))
		{
			SelectServerFocus = Apocalypse;
		}
	}

	if(X > 256 && X < (256+76)) // Cancel Button
	{
		if(Y > 282 && Y < (282+20))
		{
			SelectServerFocus = Cancel;
		}
	}
}

void SelectServerScene::OnLButtonDown(int X, int Y)
{
	if(X > 139 && X < (139+138)) // Abaddon Button
	{
		if(Y > 176 && Y < (176+19))
		{
			SelectServerFocus = Abaddon;
			Game::GetInstance().ChangeScene(new LoginScene);
		}
	}

	if(X > 131 && X < (139+157)) // Apocalypse Button
	{
		if(Y > 204 && Y < (204+19))
		{
			SelectServerFocus = Apocalypse;
		}
	}

	if(X > 256 && X < (256+76)) // Cancel Button
	{
		if(Y > 282 && Y < (282+20))
		{
			Game::GetInstance().ChangeScene(new MenuScene);
		}
	}
}

void SelectServerScene::OnKeyDown(SDLKey Sym, SDLMod Mod, Uint16 Unicode)
{
	if(Sym == SDLK_ESCAPE)
	{
		Game::GetInstance().ChangeScene(new MenuScene);
	}

	if(Sym == SDLK_RETURN)
	{
		switch(SelectServerFocus)
		{
		case Abaddon:
			Game::GetInstance().ChangeScene(new LoginScene);
			break;
		case Apocalypse:
			break;
		case Cancel:
			Game::GetInstance().ChangeScene(new MenuScene);
			break;
		}
	}

	if(Sym == SDLK_UP)
	{
		switch(SelectServerFocus)
		{
		case Abaddon:
			SelectServerFocus = Cancel;
			break;
		case Apocalypse:
			SelectServerFocus = Abaddon;
			break;
		case Cancel:
			SelectServerFocus = Apocalypse;
			break;
		}
	}

	if(Sym == SDLK_DOWN || Sym == SDLK_TAB)
	{
		switch(SelectServerFocus)
		{
		case Abaddon:
			SelectServerFocus = Apocalypse;
			break;
		case Apocalypse:
			SelectServerFocus = Cancel;
			break;
		case Cancel:
			SelectServerFocus = Abaddon;
			break;
		}
	}
}