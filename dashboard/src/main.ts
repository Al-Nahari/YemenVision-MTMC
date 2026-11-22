import {bootstrapApplication} from '@angular/platform-browser';
import {provideRouter} from '@angular/router';
import {provideHttpClient,withInterceptors} from '@angular/common/http';
import {App} from './app/app';
import {routes} from './app/routes';
import {apiKeyInterceptor} from './app/api.service';
bootstrapApplication(App,{providers:[provideRouter(routes),provideHttpClient(withInterceptors([apiKeyInterceptor]))]}).catch(console.error);
