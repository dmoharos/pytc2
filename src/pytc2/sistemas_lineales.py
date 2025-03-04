 #!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar  2 14:15:44 2023

@author: mariano
"""

import numpy as np

import matplotlib.pyplot as plt
from matplotlib import patches
from matplotlib.colors import rgb2hex
from collections import defaultdict
from scipy.signal import tf2zpk, TransferFunction, zpk2tf
import sympy as sp

from IPython.display import display, Math

from fractions import Fraction

##########################################
#%% Variables para el análisis simbólico #
##########################################

from .general import s



def simplify_n_monic(tt):
    '''
    Convierte una matriz de parámetros scattering (S) simbólica 
    al modelo de parámetros transferencia de scattering (Ts).

    Parameters
    ----------
    Spar : Symbolic Matrix
        Matriz de parámetros S.

    Returns
    -------
    Ts : Symbolic Matrix
        Matriz de parámetros de transferencia scattering.

    '''
    
    num, den = sp.fraction(sp.simplify(sp.expand(tt)))
    
    num = sp.poly(num,s)
    den = sp.poly(den,s)
    
    # lcnum = sp.LC(num)
    # lcden = sp.LC(den)
    
    k = num.LC() / den.LC()
    
    num = num.monic()
    den = den.monic()

    return( sp.Mul(k,num/den, evaluate=False) )


def parametrize_sos(num, den):
    '''
    Parameters
    ----------
    num : TYPE
        DESCRIPTION.
    den : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    Example
    -------

    num = sp.Poly((a*s + b),s)
    den = sp.Poly((c*s + d),s)
    sos_bili, w_on, Q_n, w_od, Q_d, K = parametrize_sos(num, den)

    num = sp.Poly((a*s),s)
    sos_bili1, w_on, Q_n, w_od, Q_d, K = parametrize_sos(num, den)

    num = sp.Poly((a),s)
    sos_bili2, w_on, Q_n, w_od, Q_d, K = parametrize_sos(num, den)

    num = sp.Poly((a*s**2 + b*s + c),s)
    den = sp.Poly((d*s**2 + e*s + f),s)
    sos_1, w_on, Q_n, w_od, Q_d, K = parametrize_sos(num, den)

    num = sp.Poly((a*s**2 + c**2),s)
    sos_2, w_on, Q_n, w_od, Q_d, K = parametrize_sos(num, den)

    num = sp.Poly((a*s**2 + s*b),s)
    sos_3, w_on, Q_n, w_od, Q_d, K = parametrize_sos(num, den)

    num = sp.Poly(a,s)
    sos_4, w_on, Q_n, w_od, Q_d, K = parametrize_sos(num, den)

    num = sp.Poly(a*s**2 ,s)
    sos_5, w_on, Q_n, w_od, Q_d, K = parametrize_sos(num, den)

    num = sp.Poly((b*s),s)
    sos_6, w_on, Q_n, w_od, Q_d, K = parametrize_sos(num, den)

    '''    
    
    w_od = sp.Rational('0')
    Q_d = sp.Rational('0')
    w_on = sp.Rational('0')
    Q_n = sp.Rational('0')
    K = sp.Rational('0')
    
    den_coeffs = den.all_coeffs()
    num_coeffs = num.all_coeffs()

    if len(den_coeffs) == 3:
    # only 2nd order denominators allowed
        
        w_od = sp.sqrt(den_coeffs[2]/den_coeffs[0])
        
        omega_Q = den_coeffs[1]/den_coeffs[0]
        
        Q_d = sp.simplify(sp.expand(w_od / omega_Q))
        
        k_d = den_coeffs[0]
        
        # wo-Q parametrization
        den  = sp.poly( s**2 + s * sp.Mul(w_od, 1/Q_d, evaluate=False) + w_od**2, s)


        if num.is_monomial:
            
            if num.degree() == 2:
                #pasaaltos
                
                k_n = num_coeffs[0]
                
                num  = sp.poly( s**2, s)

            elif num.degree() == 1:
                #pasabanda
                
                k_n = num_coeffs[0] * Q_d / w_od
                
                # wo-Q parametrization
                num  = sp.poly( s * w_od / Q_d , s)

            else:
                #pasabajos
                
                k_n = num_coeffs[0] / w_od**2
                
                num  = sp.poly( w_od**2, s)

                
        else:
        # no monomial
        
            if num.degree() == 2:

                if num_coeffs[1].is_zero:
                    
                    # zero at w_on
                    w_on = sp.sqrt(num_coeffs[2]/num_coeffs[0])

                    k_n = num_coeffs[0]
                
                    num  = sp.poly( s**2 + w_on**2, s)

                if num_coeffs[2].is_zero:
                
                    # zero at w=0 and at w_on
                    w_on = num_coeffs[1]/num_coeffs[0]

                    k_n = num_coeffs[0]

                    num = sp.poly( s*( s + w_on), s)
                
                else: 
                    # complete poly -> full bicuad
                
                    w_on = sp.sqrt(num_coeffs[2]/num_coeffs[0])
                
                    omega_Q = num_coeffs[1]/num_coeffs[0]
                    
                    Q_n = sp.simplify(sp.expand(w_on / omega_Q))
                    
                    k_n = num_coeffs[0]
                    
                    # wo-Q parametrization
                    num  = sp.poly( s**2 + s * sp.Mul(w_on, 1/Q_n, evaluate=False) + w_on**2, s)

            
            else:
                # only first order
                
                w_on = num_coeffs[1] / num_coeffs[0]
                
                k_n = num_coeffs[0]
                
                num  = sp.poly( s * w_on, s)

        
        K = sp.simplify(sp.expand(k_n / k_d))

    elif len(den_coeffs) == 2:
        # bilineal
        w_od = den_coeffs[1]/den_coeffs[0]
        
        k_d = den_coeffs[0]
        
        # wo-Q parametrization
        den  = sp.poly( s + w_od, s)        
    
        if num.is_monomial:
            
            if num.degree() == 1:
                
                k_n = num_coeffs[0]
                
                # wo-Q parametrization
                num = sp.poly( s, s)        

            else:
                                
                k_n = num_coeffs[0] / w_od
                
                num  = sp.poly( w_od, s)

                
        else:
        # no monomial
        
            w_on = num_coeffs[1]/num_coeffs[0]
            
            k_n = num_coeffs[0]
            
            # wo-Q parametrization
            num = sp.poly( s + w_on, s)        
    
        K = sp.simplify(sp.expand(k_n / k_d))

    return( num, den, w_on, Q_n, w_od, Q_d, K )

def tfcascade(tfa, tfb):
    """
    
    Parameters
    ----------
    tfa : TYPE
        DESCRIPTION.
    tfb : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    Example
    -------

    """
    
    tfc = TransferFunction( np.polymul(tfa.num, tfb.num), np.polymul(tfa.den, tfb.den) )

    return tfc

def tfadd(tfa, tfb):
    """
    
    Parameters
    ----------
    tfa : TYPE
        DESCRIPTION.
    tfb : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    Example
    -------

    """

    tfc = TransferFunction( np.polyadd( np.polymul(tfa.num,tfb.den),np.polymul(tfa.den,tfb.num)),
                                        np.polymul(tfa.den,tfb.den) )
    return tfc

def pretty_print_lti(num, den = None, displaystr = True):
    """
    
    Parameters
    ----------
    num : TYPE
        DESCRIPTION.
    den : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    Example
    -------

    """

    if den is None:
        this_lti = num
    else:
        this_lti = TransferFunction(num, den)
    
    num_str_aux = _build_poly_str(this_lti.num)
    den_str_aux = _build_poly_str(this_lti.den)

    strout = r'\frac{' + num_str_aux + '}{' + den_str_aux + '}'

    if displaystr:
        display(Math(strout))
    else:
        return strout

def pretty_print_bicuad_omegayq(num, den = None, displaystr = True):
    """
    
    Parameters
    ----------
    tfa : TYPE
        DESCRIPTION.
    tfb : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    Example
    -------

    """

    if den is None:
        this_sos = num.reshape((1,6))
    else:
        this_sos = np.hstack((
            np.pad(num, (3-len(num),0)),
            np.pad(den, (3-len(den),0)))
        ).reshape((1,6))
    
    num = this_sos[0,:3]
    den = this_sos[0,3:]
    
    if np.all( np.abs(num) > 0):
        # complete 2nd order, omega and Q parametrization
        num_str_aux = _build_omegayq_str(num)
    elif np.all(num[[0,2]] == 0) and num[1] > 0 :
        # bandpass style  s . k = s . H . omega/Q 
        num_str_aux = _build_omegayq_str(num, den = den)
    elif num[1] == 0 and np.all(num[[0,2]] > 0):
        # complex conj zeros style  s² + omega² 
        
        kk = num[0]
        if kk == 1.0:        
            omega = np.sqrt(num[2])
            num_str_aux = r's^2 + {:3.4g}^2'.format(omega)
        else:
            omega = np.sqrt(num[2]/kk)
            num_str_aux = r'{:3.4g}(s^2 + {:3.4g}^2)'.format(kk, omega)
        
    else:
        num_str_aux = _build_poly_str(num)
        
    
    den_str_aux = _build_omegayq_str(den)
    
    strout = r'\frac{' + num_str_aux + '}{' + den_str_aux + '}'

    if displaystr:
        display(Math(strout))
    else:   
        return strout

def pretty_print_SOS(mySOS, mode = 'default', displaystr = True):
    '''
    Los SOS siempre deben definirse como:
        
        
        mySOS= ( [ a1_1 a2_1 a3_1 b1_1 b2_1 b3_1 ]
                 [ a1_2 a2_2 a3_2 b1_2 b2_2 b3_2 ]
                 ...
                 [ a1_N a2_N a3_N b1_N b2_N b3_N ]
                )
        
        siendo:
            
                s² a1_i + s a2_i + a3_i
        T_i =  -------------------------
                s² b1_i + s b2_i + b3_i

    Parameters
    ----------
    mySOS : TYPE
        DESCRIPTION.
    mode : TYPE, optional
        DESCRIPTION. The default is 'default'.

    Raises
    ------
    ValueError
        DESCRIPTION.

    Returns
    -------
    None.

    '''

    sos_str = '' 
    
    valid_modes = ['default', 'omegayq']
    if mode not in valid_modes:
        raise ValueError('mode must be one of %s, not %s'
                         % (valid_modes, mode))
    SOSnumber, _ = mySOS.shape
    
    for ii in range(SOSnumber):
        
        if mode == "omegayq" and mySOS[ii,3] > 0:
            sos_str += r' . ' + pretty_print_bicuad_omegayq(mySOS[ii,:], displaystr = False )
        else:
            num, den = _one_sos2tf(mySOS[ii,:])
            this_tf = TransferFunction(num, den)
            sos_str += r' . ' + pretty_print_lti(this_tf, displaystr = False)

    sos_str = sos_str[2:]

    if displaystr:
        display(Math( r' ' + sos_str))
    else:
        return sos_str

def analyze_sys( all_sys, sys_name = None, img_ext = 'none', same_figs=True, annotations = True, xaxis = 'omega', fs = None):
    """ Analyzes the behavior of a linear system in terms of:
        
          * Magnitude and phase response or Bode plot
          * Pole-zero map
          * Group delay
          
        The funcion admits the system to analyze (*all_sys*) as:
            
            * one or a list of TransferFunction objects
            * a matrix defining several second order sections (SOSs).
            
        If *all_sys* is a SOS matrix, the function displays each of the SOS, 
        and the system resulting frome the cascade of all SOS.
    
    Parameters
    ----------
    all_sys : list or (Nx5) matrix
        The linear system to analyze. Wether a list of [scipy.signal.TransferFuncion](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.TransferFunction.html)
        objects or a matrix defining a cascade of SOS.
    sys_name : string or list.
        The labels or system description. Default: None
    img_ext : string  ['none', 'png', 'svg'].
        When different from 'none' the function save plot results to a file with 
        the indicated extension. Default: 'none'
    same_figs : boolean
        Use always the same figure numbers to plot results. When False, each call
        produce a new group of figures in a separate plot container. Default: True
    annotations : boolean
        Add annotations to the PZmap plot. When True, each singularity will be 
        acompanied of the value of omega (i.e. the radial distance to the origin)
        and Q (i.e. measure of proximity to the jw axis). Default: True
    xaxis = : string
        The meaning of the X axis: "omega" is measured in radians/s and is 
        preferred for analog systems. "freq" is measured in Hz (1/s) and is 
        valid for digital and analog. "norm" is a normalized version with norm
        defined by fs.
        . Default: omega
    fs : real value.
        The sampling frequency of the digital system or the norm for xaxis equal
        to "norm". Valid only if digital is True. Default: None (defined in 1/dlti.dt)
    
    Returns
    -------
    
    return_values : list
        List with three pair of fig and axis handles of each graphic displayed.

    Example
    -------

    Analyze a system with w0 = 1 rad/s and Q = sqrt(2)/2

    >>> import numpy as np
    >>> from scipy import signal as sig
    >>> from pytc2.sistemas_lineales import analyze_sys, pretty_print_bicuad_omegayq
    >>> Q = np.sqrt(2)/2
    >>> w0 = 1
    >>> # Cargamos la funcion transferencia como vectores de sus coeficientes.
    >>> num = np.array([ w0**2 ])
    >>> den = np.array([ 1., w0 / Q, w0**2 ])
    >>> H1 = sig.TransferFunction( num, den )
    >>> pretty_print_bicuad_omegayq(num,den)
    >>> analyze_sys(H1, sys_name='mi ejemplo')

    Compare the former system with two others with different Q values

    >>> Q = 5
    >>> w0 = 1
    >>> num = np.array([ w0**2 ])
    >>> den = np.array([ 1., w0 / Q, w0**2 ])
    >>> H2 = sig.TransferFunction( num, den )
    >>> analyze_sys([H1, H2], sys_name=['H1', 'H2'])

    See Also
    --------

    :func:`pretty_print_bicuad_omegayq`
    :func:`bodePlot`
    :func:`pzmap`

    """

    valid_ext = ['none', 'png', 'svg']
    if img_ext not in valid_ext:
        raise ValueError('Image extension must be one of %s, not %s'
                         % (valid_ext, img_ext))
    
    
    if isinstance(all_sys, list):
        cant_sys = len(all_sys)
    else:
        all_sys = [all_sys]
        cant_sys = 1

    if sys_name is None:
        sys_name = [str(ii) for ii in range(cant_sys)]
        
    if not isinstance(sys_name, list):
        sys_name = [sys_name]
        
    #%% BODE plots
    return_values = []
        
    if same_figs:
        fig_id = 1
    else:
        fig_id = 'none'
    axes_hdl = ()

    for ii in range(cant_sys):
        if all_sys[ii].dt is None:
            this_digital = False
        else:
            this_digital = True

        fig_id, axes_hdl = bodePlot(all_sys[ii], fig_id, axes_hdl, filter_description = sys_name[ii], digital = this_digital, xaxis = xaxis, fs = fs)


    if img_ext != 'none':
        plt.savefig('_'.join(sys_name) + '_Bode.' + img_ext, format=img_ext)

    return_values += [ [fig_id, axes_hdl] ]
    
    # fig_id = 6
    # axes_hdl = ()

    # for ii in range(cant_sys):
    #     fig_id, axes_hdl = bodePlot(all_sys[ii], fig_id, axes_hdl, filter_description = sys_name[ii])

    # axes_hdl[0].set_ylim(bottom=-3)

    # if img_ext != 'none':
    #     plt.savefig('_'.join(sys_name) + '_Bode-3db.' + img_ext, format=img_ext)


    #%% PZ Maps
    
    if same_figs:
        analog_fig_id = 2
        digital_fig_id = 3
    else:
        analog_fig_id = 'none'
        digital_fig_id = 'none'
    
    analog_axes_hdl = ()
    digital_axes_hdl = ()
    
    for ii in range(cant_sys):
    
        if isinstance(all_sys[ii], np.ndarray):
            
            thisFilter = sos2tf_analog(all_sys[ii])

            analog_fig_id, analog_axes_hdl = pzmap(thisFilter, filter_description=sys_name[ii], fig_id = analog_fig_id, axes_hdl=analog_axes_hdl, annotations = annotations, digital = digital, fs = fs)
            
        else:
                
            if all_sys[ii].dt is None:
                analog_fig_id, analog_axes_hdl = pzmap(all_sys[ii], filter_description=sys_name[ii], fig_id = analog_fig_id, axes_hdl=analog_axes_hdl, annotations = annotations)
                
            else:
                digital_fig_id, digital_axes_hdl = pzmap(all_sys[ii], filter_description=sys_name[ii], fig_id = digital_fig_id, axes_hdl=digital_axes_hdl, annotations = annotations)


    return_values += [ [analog_fig_id, analog_axes_hdl] ]
        
    return_values += [ [digital_fig_id, digital_axes_hdl] ]


    if isinstance(all_sys[ii], np.ndarray) or ( isinstance(all_sys[ii], TransferFunction) and all_sys[ii].dt is None) :
        analog_axes_hdl.legend()
        if img_ext != 'none':
            plt.figure(analog_fig_id)
            plt.savefig('_'.join(sys_name) + '_Analog_PZmap.' + img_ext, format=img_ext)
    else:
        digital_axes_hdl.legend()
        if img_ext != 'none':
            plt.figure(digital_fig_id)
            plt.savefig('_'.join(sys_name) + '_Digital_PZmap.' + img_ext, format=img_ext)

    
#    plt.show()
    
    #%% Group delay plots
    
    if same_figs:
        fig_id = 4
    else:
        fig_id = 'none'
    
    for ii in range(cant_sys):
        
        if all_sys[ii].dt is None:
            this_digital = False
        else:
            this_digital = True
        
        fig_id, axes_hdl = GroupDelay(all_sys[ii], fig_id, filter_description = sys_name[ii], digital = this_digital, xaxis = xaxis, fs = fs)
    
    return_values += [ [fig_id, axes_hdl] ]
    
    # axes_hdl.legend(sys_name)

    # axes_hdl.set_ylim(bottom=0)

    if img_ext != 'none':
        plt.savefig('_'.join(sys_name) + '_GroupDelay.'  + img_ext, format=img_ext)


    return(return_values)

def pzmap(myFilter, annotations = False, filter_description = None, fig_id='none', axes_hdl='none', digital = False, fs = 2*np.pi):
    """
    
    Parameters
    ----------
    tfa : TYPE
        DESCRIPTION.
    tfb : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    Example
    -------

    """

    if fig_id == 'none':
        fig_hdl = plt.figure()
        fig_id = fig_hdl.number
    else:
        if plt.fignum_exists(fig_id):
            fig_hdl = plt.figure(fig_id)
        else:
            fig_hdl = plt.figure(fig_id)
            fig_id = fig_hdl.number

    axes_hdl = plt.gca()
    
        # Get the poles and zeros
    z, p, k = tf2zpk(myFilter.num, myFilter.den)


    # Add unit circle and zero axes    
    unit_circle = patches.Circle((0,0), radius=1, fill=False,
                                 color='gray', ls='dotted', lw = 2)
    axes_hdl.add_patch(unit_circle)
    plt.axvline(0, color='0.7')
    plt.axhline(0, color='0.7')

    
    #Add circle lines
    
#        maxRadius = np.abs(10*np.sqrt(p[0]))
    
    
    # Plot the poles and set marker properties
    if filter_description is None:
        poles = plt.plot(p.real, p.imag, 'x', markersize=9)
    else:
        poles = plt.plot(p.real, p.imag, 'x', markersize=9, label=filter_description)
    
    # Plot the zeros and set marker properties
    zeros = plt.plot(z.real, z.imag,  'o', markersize=9, 
             color='none',
             markeredgecolor=poles[0].get_color(), # same color as poles
             markerfacecolor='white'
             )

    # add info to poles and zeros
    # first with poles
    w0, aux_idx = np.unique(np.abs(p), return_index=True)
    qq = 1 / (2*np.cos(np.pi - np.angle(p[aux_idx])))
   
    # label distance to the datapoint
    lab_mod = 40 
    
    # sign alternance for conjugate complex sing.
    aux_sign = np.sign(np.random.uniform(-1,1))
    
    for ii in range(len(w0)):

        rand_dir = np.random.uniform(0,2*np.pi)
        
        xy_coorde =   (lab_mod *  np.cos(rand_dir), lab_mod *  np.sin(rand_dir))
        
        if(xy_coorde[0] < 0.0):
            halign = 'left'
        else:
            halign = 'right'

        if(xy_coorde[1] < 0.0):
            valign = 'top'
        else:
            valign = 'bottom'
        
        # print(np.sqrt(np.sum(np.array(xy_coorde)**2)))
        
        if p[aux_idx[ii]].imag > 0.0:
            # annotate with Q only complex conj singularities
            
            
            aux_sign = aux_sign * -1
            
            circle = patches.Circle((0,0), radius=w0[ii], color = poles[0].get_color(), fill=False, ls= (0, (1, 10)), lw = 0.7)
            
            axes_hdl.add_patch(circle)
            plt.axvline(0, color='0.7')
            plt.axhline(0, color='0.7')
    
            if annotations:
                axes_hdl.annotate('$\omega$ = {:3.3g} \n Q = {:3.3g}'.format(w0[ii], qq[ii]),
                            xy=(p[aux_idx[ii]].real, p[aux_idx[ii]].imag * aux_sign), xycoords='data',
                            xytext = xy_coorde, textcoords='offset points',
                            arrowprops=dict(facecolor= poles[0].get_color(), shrink=0.15,
                                            width = 1, headwidth = 5 ),
                            horizontalalignment = halign, verticalalignment = valign,
                            color=poles[0].get_color(),
                            bbox=dict(edgecolor=poles[0].get_color(), facecolor=_complementaryColor(rgb2hex(poles[0].get_color())), alpha=0.4))
    
        else:
            # annotate with omega real singularities
            
            if annotations:
                axes_hdl.annotate('$\omega$ = {:3.3g}'.format(w0[ii]),
                            xy=(p[aux_idx[ii]].real, p[aux_idx[ii]].imag) , xycoords='data',
                            xytext = xy_coorde, textcoords='offset points',
                            arrowprops=dict(facecolor= poles[0].get_color(), shrink=0.15,
                                            width = 1, headwidth = 5 ),
                            horizontalalignment = halign, verticalalignment = valign,
                            color=poles[0].get_color(),
                            bbox=dict(edgecolor=poles[0].get_color(), facecolor=_complementaryColor(rgb2hex(poles[0].get_color())), alpha=0.4) )
            

    # and then zeros
    w0, aux_idx = np.unique(np.abs(z), return_index=True)
    qq = 1 / (2*np.cos(np.pi - np.angle(z[aux_idx])))

    # sign alternance for conjugate complex sing.
    aux_sign = np.sign(np.random.uniform(-1,1))

    for ii in range(len(w0)):

        aux_sign = aux_sign * -1

        rand_dir = np.random.uniform(0, 2*np.pi)
        
        xy_coorde = (lab_mod *  np.cos(rand_dir), lab_mod *  np.sin(rand_dir))

        if(xy_coorde[0] < 0.0):
            halign = 'left'
        else:
            halign = 'right'

        if(xy_coorde[1] < 0.0):
            valign = 'top'
        else:
            valign = 'bottom'

        if z[aux_idx[ii]].imag > 0.0:
            
            circle = patches.Circle((0,0), radius=w0[ii], color = poles[0].get_color(), fill=False, ls= (0, (1, 10)), lw = 0.7)
            
            axes_hdl.add_patch(circle)
            plt.axvline(0, color='0.7')
            plt.axhline(0, color='0.7')
    
            if annotations:
                axes_hdl.annotate('$\omega$ = {:3.3g} \n Q = {:3.3g}'.format(w0[ii], qq[ii]),
                            xy=(z[aux_idx[ii]].real, z[aux_idx[ii]].imag * aux_sign), xycoords='data',
                            xytext = xy_coorde, textcoords='offset points',
                            arrowprops=dict(facecolor=poles[0].get_color(), shrink=0.15,
                                            width = 1, headwidth = 5 ),
                            horizontalalignment = halign, verticalalignment = valign,
                            color=poles[0].get_color(),
                            bbox=dict(boxstyle = 'Circle', edgecolor=poles[0].get_color(), facecolor=None, alpha=0.4) )
    
        else:
            # annotate with omega real singularities
            
            if annotations:
                axes_hdl.annotate('$\omega$ = {:3.3g}'.format(w0[ii]),
                            xy=(z[aux_idx[ii]].real, z[aux_idx[ii]].imag), xycoords='data',
                            xytext = xy_coorde, textcoords='offset points',
                            arrowprops=dict(facecolor=poles[0].get_color(), shrink=0.15,
                                            width = 1, headwidth = 5 ),
                            horizontalalignment = halign, verticalalignment = valign,
                            color=poles[0].get_color(),
                            bbox=dict(boxstyle = 'Circle', edgecolor=poles[0].get_color(), facecolor=None, alpha=0.4) )


    # Scale axes to fit
    r_old = axes_hdl.get_ylim()[1]
    
    r = 1.1 * np.amax(np.concatenate(([r_old/1.1], abs(z), abs(p), [1])))
    plt.axis('scaled')
    plt.axis([-r, r, -r, r])
#    ticks = [-1, -.5, .5, 1]
#    plt.xticks(ticks)
#    plt.yticks(ticks)

    """
    If there are multiple poles or zeros at the same point, put a 
    superscript next to them.
    TODO: can this be made to self-update when zoomed?
    """
    # Finding duplicates by same pixel coordinates (hacky for now):
    poles_xy = axes_hdl.transData.transform(np.vstack(poles[0].get_data()).T)
    zeros_xy = axes_hdl.transData.transform(np.vstack(zeros[0].get_data()).T)    

    # dict keys should be ints for matching, but coords should be floats for 
    # keeping location of text accurate while zooming

    

    d = defaultdict(int)
    coords = defaultdict(tuple)
    for xy in poles_xy:
        key = tuple(np.rint(xy).astype('int'))
        d[key] += 1
        coords[key] = xy
    for key, value in d.items():
        if value > 1:
            x, y = axes_hdl.transData.inverted().transform(coords[key])
            plt.text(x, y, 
                        r' ${}^{' + str(value) + '}$',
                        fontsize=13,
                        )

    d = defaultdict(int)
    coords = defaultdict(tuple)
    for xy in zeros_xy:
        key = tuple(np.rint(xy).astype('int'))
        d[key] += 1
        coords[key] = xy
    for key, value in d.items():
        if value > 1:
            x, y = axes_hdl.transData.inverted().transform(coords[key])
            plt.text(x, y, 
                        r' ${}^{' + str(value) + '}$',
                        fontsize=13,
                        )

    if myFilter.dt is None:
        digital = False
    else:
        digital = True
    
    if digital:
        plt.xlabel(r'$\Re(z)$')
        plt.ylabel(r'$\Im(z)$')
    else:
        plt.xlabel(r'$\sigma$')
        plt.ylabel('j'+r'$\omega$')

    plt.grid(True, color='0.9', linestyle='-', which='both', axis='both')

    fig_hdl.suptitle('Poles and Zeros map')

    if not(filter_description is None):
       axes_hdl.legend()

    return fig_id, axes_hdl
    
     
def group_delay( freq, phase):
    """
    Calcula el retardo de grupo para una función de fase.
    
    Parameters
    ----------
    freq : NP array
        La grilla de frecuencia a la que se calcula la fase.
    phase : NP array
        La fase de la función a calcular el retardo de grupo.

    Returns
    -------
    gd : NP array.
        Devuelve una estimación de la derivada de la fase 
        respecto a la frecuencia cambiada de signo (retardo 
        de grupo).

    Example
    -------

    """
    
    groupDelay = -np.diff(phase)/np.diff(freq)
    
    return(np.append(groupDelay, groupDelay[-1]))
    
    
def GroupDelay(myFilter, fig_id='none', filter_description=None, npoints = 1000, digital = False, xaxis = 'omega', fs = 2*np.pi):
    """
    
    Parameters
    ----------
    tfa : TYPE
        DESCRIPTION.
    tfb : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    Example
    -------

    """
    
    if isinstance(myFilter, np.ndarray):
        # SOS section
        cant_sos = myFilter.shape[0]
        phase = np.empty((npoints, cant_sos+1))
        sos_label = []
        
        for ii in range(cant_sos):
            
            num, den = _one_sos2tf(myFilter[ii,:])
            thisFilter = TransferFunction(num, den)

            this_zzpp = np.abs(np.concatenate([thisFilter.zeros, thisFilter.poles]))
            this_zzpp = this_zzpp[this_zzpp > 0]
            
            if digital:
                w, _, phase[:,ii] = thisFilter.bode(np.linspace(0, np.pi, npoints))
            else:
                w, _, phase[:,ii] = thisFilter.bode(np.logspace(np.floor(np.log10(np.min(this_zzpp)))-1, np.ceil(np.log10(np.max(this_zzpp))) + 1 ,npoints))
            
            sos_label += [filter_description + ' - SOS {:d}'.format(ii)]
        
        # whole filter
        thisFilter = sos2tf_analog(myFilter)

        this_zzpp = np.abs(np.concatenate([thisFilter.zeros, thisFilter.poles]))
        this_zzpp = this_zzpp[this_zzpp > 0]
        
        if digital:
            w, _, phase[:,cant_sos] = thisFilter.bode(np.linspace(0, np.pi, npoints))
        else:
            w, _, phase[:,cant_sos] = thisFilter.bode(np.logspace(np.floor(np.log10(np.min(this_zzpp)))-1, np.ceil(np.log10(np.max(this_zzpp))) + 1 ,npoints))
        
        # if digital:
        #     w, _, phase[:,cant_sos] = thisFilter.bode(np.linspace(10**-2, w_nyq, npoints))
        # else:
        #     w, _, phase[:,cant_sos] = thisFilter.bode(np.logspace(-2,2,npoints))
        
        sos_label += [filter_description]
        
        filter_description = sos_label

        phaseRad = phase * np.pi / 180.0
    
        phaseRad = phaseRad.reshape((npoints, 1+cant_sos))
        
        # filter gaps and jumps
        all_jump_x, all_jump_y = (np.abs(np.diff(phaseRad, axis = 0)) > 4/5*np.pi).nonzero()

        for this_jump_x, this_jump_y in zip(all_jump_x, all_jump_y ):
            phaseRad[this_jump_x+1:, this_jump_y] = phaseRad[this_jump_x+1:, this_jump_y]  - np.pi
        
    else:
        # LTI object
        cant_sos = 0
        
        this_zzpp = np.abs(np.concatenate([myFilter.zeros, myFilter.poles]))
        this_zzpp = this_zzpp[this_zzpp > 0]
        
        if digital:
            w, _, phase = myFilter.bode(np.linspace(0, np.pi, npoints))
        else:
            w, _, phase = myFilter.bode(np.logspace(np.floor(np.log10(np.min(this_zzpp)))-1, np.ceil(np.log10(np.max(this_zzpp))) + 1 ,npoints))

        phaseRad = phase * np.pi / 180.0

        phaseRad = phaseRad.reshape((npoints, 1))

        # filter gaps and jumps
        all_jump = np.where(np.abs(np.diff(phaseRad, axis = 0)) > 4/5*np.pi)[0]

        for this_jump_x in all_jump:
            phaseRad[this_jump_x+1:] = phaseRad[this_jump_x+1] - np.pi
        
        # if myFilter.dt is None:
        #     w, _, phase = myFilter.bode(np.logspace(-2,2,npoints))
        # else:
        #     digital = True
        #     w, _, phase = myFilter.bode(np.linspace(10**-2, w_nyq, npoints))
        
        # if isinstance(filter_description, str):
        #     filter_description = [filter_description]
    
    groupDelay = -np.diff(phaseRad, axis = 0) / np.diff(w).reshape((npoints-1,1))

    # ww ya está en rad/s
    if xaxis == "freq":
        # to Hz
        ww = w / 2 / np.pi
    elif xaxis == "norm":
        if fs is None:
            # normalizar cada respuesta a su propio nyqyuist
            wnorm = 2*np.pi/myFilter.dt/2
        else:
            # normalizado a fs
            wnorm = 2*np.pi*fs
            
        ww = w / wnorm
    else:
        ww = w


    if fig_id == 'none':
        fig_hdl = plt.figure()
        fig_id = fig_hdl.number
    else:
        if plt.fignum_exists(fig_id):
            fig_hdl = plt.figure(fig_id)
        else:
            fig_hdl = plt.figure(fig_id)
            fig_id = fig_hdl.number

    if digital:
        aux_hdl = plt.plot(ww[1:], groupDelay, label=filter_description)    # Bode phase plot
    else:
        aux_hdl = plt.semilogx(ww[1:], groupDelay, label=filter_description)    # Bode phase plot

    if cant_sos > 0:
        # distinguish SOS from total response
        [ aa.set_linestyle(':') for aa in  aux_hdl[:-1]]
        aux_hdl[-1].set_linewidth(2)
    
    plt.grid(True)
    
    
    
    if xaxis == "freq":
        # to Hz
        plt.xlabel('Frequency [Hz]')
    elif xaxis == "norm":
        # normalizado a fs
        plt.gca().set_xlim([0, 1])

        if fs is None:
            # normalizar cada respuesta a su propio nyqyuist
            this_fs = 1/myFilter.dt
        else:
            # normalizado a fs
            this_fs = fs
        
        plt.xlabel('Frecuencia normalizada a fs={:3.3f} [#]'.format(this_fs))
    else:
        plt.xlabel('Angular frequency [rad/sec]')
    

    
    plt.ylabel('Group Delay [sec]')
    plt.title('Group delay')

    axes_hdl = plt.gca()
    
    if not(filter_description is None):
        # axes_hdl.legend( filter_description )
        axes_hdl.legend()

    return fig_id, axes_hdl

def bodePlot(myFilter, fig_id='none', axes_hdl='none', filter_description=None, npoints = 1000, digital = False, xaxis = 'omega', fs = 2*np.pi ):
    """
    
    Parameters
    ----------
    tfa : TYPE
        DESCRIPTION.
    tfb : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    Example
    -------

    """
    
    if isinstance(myFilter, np.ndarray):
        # SOS section
        
        wholeFilter = sos2tf_analog(myFilter)

        # all singularities
        this_zzpp = np.abs(np.concatenate([wholeFilter.zeros, wholeFilter.poles]))
        this_zzpp = this_zzpp[this_zzpp > 0]

        # calculate the omega axis according to singularities of the whole filter
        if digital:
            ww = np.linspace(0, np.pi, npoints)
        else:
            ww = np.logspace(np.floor(np.log10(np.min(this_zzpp)))-1, np.ceil(np.log10(np.max(this_zzpp))) + 1 ,npoints)
        
        cant_sos = myFilter.shape[0]
        mag = np.empty((npoints, cant_sos+1))
        phase = np.empty_like(mag)
        sos_label = []
        
        for ii in range(cant_sos):
            
            num, den = _one_sos2tf(myFilter[ii,:])
            thisFilter = TransferFunction(num, den)
            
            this_zzpp = np.abs(np.concatenate([thisFilter.zeros, thisFilter.poles]))
            this_zzpp = this_zzpp[this_zzpp > 0]

            _, mag[:, ii], phase[:,ii] = thisFilter.bode(ww)
                
            
            sos_label += [filter_description + ' - SOS {:d}'.format(ii)]
        
        # whole filter
        _, mag[:, cant_sos], phase[:,cant_sos] = wholeFilter.bode(ww)

        sos_label += [filter_description]
        
        filter_description = sos_label
        
    else:
        # LTI object
        cant_sos = 0
        
        this_zzpp = np.abs(np.concatenate([myFilter.zeros, myFilter.poles]))
        this_zzpp = this_zzpp[this_zzpp > 0]
        
        if digital:
            ww, mag, phase = myFilter.bode(n=np.linspace(0, np.pi, npoints))
                
        else:
            ww, mag, phase = myFilter.bode(np.logspace(np.floor(np.log10(np.min(this_zzpp)))-1, np.ceil(np.log10(np.max(this_zzpp))) + 1 ,npoints))
        
        # if myFilter.dt is None:
        #     # filtro analógico normalizado
        #     ww, mag, phase = myFilter.bode(np.logspace(-2,2,npoints))
        # else:
        #     ww, mag, phase = myFilter.bode(np.linspace(10**-2, ww_nyq, npoints))
        
        # if isinstance(filter_description, str):
        #     filter_description = [filter_description]
        

    # ww ya está en rad/s
    if xaxis == "freq":
        # to Hz
        ww = ww / 2 / np.pi
    elif xaxis == "norm":
        if fs is None:
            # normalizar cada respuesta a su propio nyqyuist
            wnorm = 2*np.pi/myFilter.dt/2
        else:
            # normalizado a fs
            wnorm = 2*np.pi*fs
        ww = ww / wnorm

    if fig_id == 'none':
        fig_hdl, axes_hdl = plt.subplots(2, 1, sharex='col')
        fig_id = fig_hdl.number
    else:
        if plt.fignum_exists(fig_id):
            fig_hdl = plt.figure(fig_id)
            axes_hdl = fig_hdl.get_axes()
        else:
            fig_hdl = plt.figure(fig_id)
            axes_hdl = fig_hdl.subplots(2, 1, sharex='col')
            fig_id = fig_hdl.number

    (mag_ax_hdl, phase_ax_hdl) = axes_hdl
    
    plt.sca(mag_ax_hdl)

    if digital:
        if filter_description is None:
            aux_hdl = plt.plot(ww, mag)    # Bode magnitude plot
        else:
            aux_hdl = plt.plot(ww, mag, label=filter_description)    # Bode magnitude plot
    else:
        if filter_description is None:
            aux_hdl = plt.semilogx(ww, mag)    # Bode magnitude plot
        else:
            aux_hdl = plt.semilogx(ww, mag, label=filter_description)    # Bode magnitude plot
    
    if cant_sos > 0:
        # distinguish SOS from total response
        [ aa.set_linestyle(':') for aa in  aux_hdl[:-1]]
        aux_hdl[-1].set_linewidth(2)
    
    plt.grid(True)
#    plt.xlabel('Angular frequency [rad/sec]')
    plt.ylabel('Magnitude [dB]')
    plt.title('Magnitude response')
    
    if not(filter_description is None):
        # mag_ax_hdl.legend( filter_description )
        mag_ax_hdl.legend()

        
    plt.sca(phase_ax_hdl)
    
    if digital:
        if filter_description is None:
            aux_hdl = plt.plot(ww, np.pi/180*phase)    # Bode phase plot
        else:
            aux_hdl = plt.plot(ww, np.pi/180*phase, label=filter_description)    # Bode phase plot
            
    else:
        if filter_description is None:
            aux_hdl = plt.semilogx(ww, np.pi/180*phase)    # Bode phase plot
        else:
            aux_hdl = plt.semilogx(ww, np.pi/180*phase, label=filter_description)    # Bode phase plot
    
    
    # Scale axes to fit
    ylim = plt.gca().get_ylim()

    # presentar la fase como fracciones de \pi
    ticks = np.linspace(start=np.round(ylim[0]/np.pi)*np.pi, stop=np.round(ylim[1]/np.pi)*np.pi, num = 5, endpoint=True)

    ylabs = []
    for aa in ticks:
        
        if aa == 0:
            ylabs += ['0'] 
        else:
            bb = Fraction(aa/np.pi).limit_denominator(1000000)
            if np.abs(bb.numerator) != 1:
                if np.abs(bb.denominator) != 1:
                    str_aux = r'$\frac{{{:d}}}{{{:d}}} \pi$'.format(bb.numerator, bb.denominator)
                else:
                    str_aux = r'${:d}\pi$'.format(bb.numerator)
                    
            else:
                if np.abs(bb.denominator) == 1:
                    if np.sign(bb.numerator) == -1:
                        str_aux = r'$-\pi$'
                    else:
                        str_aux = r'$\pi$'
                else:
                    if np.sign(bb.numerator) == -1:
                        str_aux = r'$-\frac{{\pi}}{{{:d}}}$'.format(bb.denominator)
                    else:
                        str_aux = r'$\frac{{\pi}}{{{:d}}}$'.format(bb.denominator)
                    
            ylabs += [ str_aux ]
            
    plt.yticks(ticks, labels = ylabs )
    
    if cant_sos > 0:
        # distinguish SOS from total response
        [ aa.set_linestyle(':') for aa in  aux_hdl[:-1]]
        aux_hdl[-1].set_linewidth(2)
    
    plt.grid(True)

    if xaxis == "freq":
        # to Hz
        plt.xlabel('Frequency [Hz]')
        
    elif xaxis == "norm":
        # normalizado a fs
        plt.gca().set_xlim([0, 1])
        
        if fs is None:
            # normalizar cada respuesta a su propio nyqyuist
            this_fs = 1/myFilter.dt
        else:
            # normalizado a fs
            this_fs = fs
        
        plt.xlabel('Frecuencia normalizada a fs={:3.3f} [#]'.format(this_fs))
    else:
        plt.xlabel('Angular frequency [rad/sec]')
        
        
    plt.ylabel('Phase [rad]')
    plt.title('Phase response')
    
    if not(filter_description is None):
        # phase_ax_hdl.legend( filter_description )
        phase_ax_hdl.legend()
    
    return fig_id, axes_hdl

def plot_plantilla(filter_type = 'lowpass', fpass = 0.25, ripple = 0.5, fstop = 0.6, attenuation = 40, fs = 2 ):
    """
    
    Parameters
    ----------
    tfa : TYPE
        DESCRIPTION.
    tfb : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    Example
    -------

    """
    
    # para sobreimprimir la plantilla de diseño de un filtro
    
    xmin, xmax, ymin, ymax = plt.axis()
    
    # banda de paso digital
    plt.fill([xmin, xmin, fs/2, fs/2],   [ymin, ymax, ymax, ymin], 'g', alpha= 0.2, lw=1, label = 'bw digital') # pass
    
    if filter_type == 'lowpass':
    
        fstop_start = fstop
        fstop_end = xmax
        
        fpass_start = xmin
        fpass_end   = fpass
    
        plt.fill( [fstop_start, fstop_end,   fstop_end, fstop_start], [-attenuation, -attenuation, ymax, ymax], '0.9', lw=1, ls = '--', ec = 'k', label = 'plantilla') # stop
        plt.fill( [fpass_start, fpass_start, fpass_end, fpass_end],   [ymin, -ripple, -ripple, ymin], '0.9', lw=1, ls = '--', ec = 'k') # pass
    
    elif filter_type == 'highpass':
    
        fstop_start = xmin
        fstop_end = fstop 
        
        fpass_start = fpass
        fpass_end   = xmax
    
        plt.fill( [fstop_start, fstop_end,   fstop_end, fstop_start], [-attenuation, -attenuation, ymax, ymax], '0.9', lw=1, ls = '--', ec = 'k', label = 'plantilla') # stop
        plt.fill( [fpass_start, fpass_start, fpass_end, fpass_end],   [ymin, -ripple, -ripple, ymin], '0.9', lw=1, ls = '--', ec = 'k') # pass
    
    
    elif filter_type == 'bandpass':
    
        fstop_start = xmin
        fstop_end = fstop[0]
        
        fpass_start = fpass[0]
        fpass_end   = fpass[1]
        
        fstop2_start = fstop[1]
        fstop2_end =  xmax
        
        plt.fill( [fstop_start, fstop_end,   fstop_end, fstop_start], [-attenuation, -attenuation, ymax, ymax], '0.9', lw=1, ls = '--', ec = 'k', label = 'plantilla') # stop
        plt.fill( [fpass_start, fpass_start, fpass_end, fpass_end],   [ymin, -ripple, -ripple, ymin], '0.9', lw=1, ls = '--', ec = 'k') # pass
        plt.fill( [fstop2_start, fstop2_end,   fstop2_end, fstop2_start], [-attenuation, -attenuation, ymax, ymax], '0.9', lw=1, ls = '--', ec = 'k') # stop
        
    elif filter_type == 'bandstop':
    
        fpass_start = xmin
        fpass_end   = fpass[0]
    
        fstop_start = fstop[0]
        fstop_end = fstop[1]
        
        fpass2_start = fpass[1]
        fpass2_end   = xmax
            
        plt.fill([fpass_start, fpass_start, fpass_end, fpass_end],   [ymin, -ripple, -ripple, ymin], '0.9', lw=1, ls = '--', ec = 'k', label = 'plantilla') # pass
        plt.fill([fstop_start, fstop_end,   fstop_end, fstop_start], [-attenuation, -attenuation, ymax, ymax], '0.9', lw=1, ls = '--', ec = 'k') # stop
        plt.fill([fpass2_start, fpass2_start, fpass2_end, fpass2_end],   [ymin, -ripple, -ripple, ymin], '0.9', lw=1, ls = '--', ec = 'k') # pass
    
    
    plt.axis([xmin, xmax, np.max([ymin, -100]), np.max([ymax, 5])])
    
    # axes_hdl = plt.gca()
    # axes_hdl.legend()
    
    # plt.show()
    
def sos2tf_analog(mySOS):
    """
    
    Parameters
    ----------
    tfa : TYPE
        DESCRIPTION.
    tfb : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    Example
    -------

    """
    
    SOSnumber, _ = mySOS.shape
    
    num = 1
    den = 1
    
    for ii in range(SOSnumber):
        
        sos_num, sos_den = _one_sos2tf(mySOS[ii,:])
        num = np.polymul(num, sos_num)
        den = np.polymul(den, sos_den)

    tf = TransferFunction(num, den)
    
    return tf

def tf2sos_analog(num, den, pairing='nearest'):
    """
    
    Parameters
    ----------
    tfa : TYPE
        DESCRIPTION.
    tfb : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    Example
    -------

    """

    z, p, k = tf2zpk(num, den)
    
    sos = zpk2sos_analog(z, p, k, pairing = pairing)

    return sos
        
def zpk2sos_analog(zz, pp, kk, pairing='nearest'):
    """
    From scipy.signal, modified by marianux
    ----------------------------------------
    
    Return second-order sections from zeros, poles, and gain of a system
    
    Parameters
    ----------
    z : array_like
        Zeros of the transfer function.
    p : array_like
        Poles of the transfer function.
    k : float
        System gain.
    pairing : {'nearest', 'keep_odd'}, optional
        The method to use to combine pairs of poles and zeros into sections.
        See Notes below.

    Returns
    -------
    sos : ndarray
        Array of second-order filter coefficients, with shape
        ``(n_sections, 6)``. See `sosfilt` for the SOS filter format
        specification.

    See Also
    --------
    sosfilt

    Notes
    -----
    The algorithm used to convert ZPK to SOS format follows the suggestions
    from R. Schaumann's "Design of analog filters". Ch. 5:
        1- Assign zeros to closest poles
        2- order sections by increasing Q
        3- gains ordering to maximize dynamic range. See ch. 5.

  
    """
    
    # if empty filter then
    if len(zz) == len(pp) == 0:
        return np.array([[0., 0., kk, 1., 0., 0.]])

    assert len(zz) <= len(pp), "Filter must have more poles than zeros"
    
    n_sections = ( len(pp) + 1) // 2
    sos = np.zeros((n_sections, 6))

    # Ensure we have complex conjugate pairs
    # (note that _cplxreal only gives us one element of each complex pair):
    z = np.concatenate(_cplxreal(zz))
    p = np.concatenate(_cplxreal(pp))

    # calculate los omega_0 and Q for each pole
    # w0 = np.abs(p)
    qq = 1 / (2*np.cos(np.pi - np.angle(p)))

    p_sos = np.zeros((n_sections, 2), np.complex128)
    z_sos = np.zeros_like(p_sos)
    
    if n_sections == z.shape[0]:
        one_z_per_section = True
    else:
        one_z_per_section = False
            
    
    for si in range(n_sections):
        # Select the next "worst" pole
        p1_idx = np.argmax(qq)
            
        p1 = p[p1_idx]
        p = np.delete(p, p1_idx)
        qq = np.delete(qq, p1_idx)

        # Pair that pole with a zero

        if np.isreal(p1) and np.isreal(p).sum() == 0:
            # Special case to set a first-order section
            if z.size == 0:
                # no zero, just poles
                z1 = np.nan

            else:            
                z1_idx = _nearest_real_complex_idx(z, p1, 'real')
                z1 = z[z1_idx]
                z = np.delete(z, z1_idx)
                
            p2 = z2 = np.nan
            
        else:
            # SOS 
            
            if z.size == 0:
                # no zero, just poles
                z1 = np.nan
                
            else:
                # Pair the pole with the closest zero (real or complex)
                z1_idx = np.argmin(np.abs(p1 - z))
                z1 = z[z1_idx]
                z = np.delete(z, z1_idx)

            # Now that we have p1 and z1, figure out what p2 and z2 need to be
            
            if np.isnan(z1):
                # no zero, just poles
                z2 = np.nan
                
                if np.isreal(p1):
                    # pick the next "worst" pole to use
                    idx = np.nonzero(np.isreal(p))[0]
                    assert len(idx) > 0
                    p2_idx = idx[np.argmax(qq)]
                    p2 = p[p2_idx]
                    p = np.delete(p, p2_idx)

                else:
                    # complex pole
                    p2 = p1.conj()

                
            else:
                # there are zero/s for z2
                    
                if np.isreal(p1):
                    
                    if np.isreal(z1):  
                        
                        # real pole, real zero
                        # pick the next "worst" pole to use
                        idx = np.nonzero(np.isreal(p))[0]
                        assert len(idx) > 0
                        p2_idx = idx[np.argmin(np.abs(np.abs(p[idx]) - 1))]
                        p2 = p[p2_idx]
                        # find a real zero to match the added pole
                        assert np.isreal(p2)
                        
                        if one_z_per_section or len(z) == 0:
                            # avoid picking double zero (high-pass)
                            # prefer picking band-pass sections (Schaumann 5.3.1)
                            z2 = np.nan
                        else:
                            z2_idx = _nearest_real_complex_idx(z, p2, 'real')
                            z2 = z[z2_idx]
                            assert np.isreal(z2)
                            z = np.delete(z, z2_idx)
                        
                    else:  

                        # real pole, complex zero
                        z2 = z1.conj()
                        p2_idx = _nearest_real_complex_idx(p, z1, 'real')
                        p2 = p[p2_idx]
                        assert np.isreal(p2)

                    p = np.delete(p, p2_idx)
                    
                else:
                    # complex pole

                    p2 = p1.conj()
                    
                    if np.isreal(z1):  # complex pole, complex zero

                        # complex pole, real zero -> possible bandpass
                        
                        if one_z_per_section or len(z) == 0:
                            # avoid picking double zero (high-pass)
                            # prefer picking band-pass sections (Schaumann 5.3.1)
                            z2 = np.nan
                        else:
                            # z1 over the \sigma axis
                            z2_idx = _nearest_real_complex_idx(z, p1, 'real')
                            z2 = z[z2_idx]
                            assert np.isreal(z2)
                            z = np.delete(z, z2_idx)

                    else:  
                        # complex pole, complex zero -> SOS
                        
                        z2 = z1.conj()
                    
        p_sos[si] = [p1, p2]
        z_sos[si] = [z1, z2]
        
    assert len(p) == 0  # we've consumed all poles and zeros
    del p, z

    # Construct the system, reversing order so the "worst" are last
    p_sos = np.reshape(p_sos[::-1], (n_sections, 2))
    z_sos = np.reshape(z_sos[::-1], (n_sections, 2))
    
    # asignación de ganancias para cada SOS
    mmi = np.ones(n_sections)
    gains = np.ones(n_sections, np.array(kk).dtype)
    
    tf_j = TransferFunction(1.0, 1.0)
    
    for si in range(n_sections):
        
        this_zz = z_sos[si, np.logical_not( np.isnan(z_sos[si])) ]
        this_pp = p_sos[si, np.logical_not(np.isnan(p_sos[si]))]
        
        num, den = zpk2tf(this_zz, this_pp, 1) # no gain
        
        tf_j = tfcascade(tf_j, TransferFunction(num, den))

        this_zzpp = np.abs(np.concatenate([this_zz, this_pp]))
        this_zzpp = this_zzpp[this_zzpp > 0]
        
        _, mag, _ = tf_j.bode(np.logspace(np.floor(np.log10(np.min(this_zzpp)))-2, np.ceil(np.log10(np.max(this_zzpp)))+2, 100))
        
        # bode in dB
        mmi[si] = 10**(np.max(mag)/20) # M_i according to Schaumann eq 5.76
    

    # first gain to optimize dynamic range.
    gains[0] = kk * (mmi[-1]/mmi[0])

    for si in range(n_sections):

        if si > 0:
            gains[si] = (mmi[si-1]/mmi[si])

        num, den = zpk2tf(z_sos[si, np.logical_not(np.isnan(z_sos[si])) ], p_sos[si, np.logical_not(np.isnan(p_sos[si]))], gains[si]) # now with gain
        
        num = np.concatenate((np.zeros(np.max(3 - len(num), 0)), num))
        den = np.concatenate((np.zeros(np.max(3 - len(den), 0)), den))
            
        sos[si] = np.concatenate((num,den))
        
        
    # verify the factorization
    tf_verif = sos2tf_analog(sos)
    z_v, p_v, k_v = tf2zpk(tf_verif.num, tf_verif.den)
    
    num_t, den_t = zpk2tf(zz, pp, kk)
    
    if np.std(num_t - tf_verif.num) > 1e-10:

        raise ValueError('Incorrect factorization: Zeros does not match')

    if np.std(den_t - tf_verif.den) > 1e-10:

        raise ValueError('Incorrect factorization: Poles does not match')
        
        
    return sos
    
########################
#%% Funciones internas #
########################

def _nearest_real_complex_idx(fro, to, which):
    '''
    Get the next closest real or complex element based on distance
    
    Parameters
    ----------
    Spar : Symbolic Matrix
        Matriz de parámetros S.

    Returns
    -------
    Ts : Symbolic Matrix
        Matriz de parámetros de transferencia scattering.

    '''
    
    assert which in ('real', 'complex')
    order = np.argsort(np.abs(fro - to))
    mask = np.isreal(fro[order])
    if which == 'complex':
        mask = ~mask
    return order[np.nonzero(mask)[0][0]]

def _cplxreal(z, tol=None):
    """
    Split into complex and real parts, combining conjugate pairs.

    The 1-D input vector `z` is split up into its complex (`zc`) and real (`zr`)
    elements. Every complex element must be part of a complex-conjugate pair,
    which are combined into a single number (with positive imaginary part) in
    the output. Two complex numbers are considered a conjugate pair if their
    real and imaginary parts differ in magnitude by less than ``tol * abs(z)``.

    Parameters
    ----------
    z : array_like
        Vector of complex numbers to be sorted and split
    tol : float, optional
        Relative tolerance for testing realness and conjugate equality.
        Default is ``100 * spacing(1)`` of `z`'s data type (i.e., 2e-14 for
        float64)

    Returns
    -------
    zc : ndarray
        Complex elements of `z`, with each pair represented by a single value
        having positive imaginary part, sorted first by real part, and then
        by magnitude of imaginary part. The pairs are averaged when combined
        to reduce error.
    zr : ndarray
        Real elements of `z` (those having imaginary part less than
        `tol` times their magnitude), sorted by value.

    Raises
    ------
    ValueError
        If there are any complex numbers in `z` for which a conjugate
        cannot be found.

    See Also
    --------
    _cplxpair

    Examples
    --------
    >>> a = [4, 3, 1, 2-2j, 2+2j, 2-1j, 2+1j, 2-1j, 2+1j, 1+1j, 1-1j]
    >>> zc, zr = _cplxreal(a)
    >>> print(zc)
    [ 1.+1.j  2.+1.j  2.+1.j  2.+2.j]
    >>> print(zr)
    [ 1.  3.  4.]
    """

    z = np.atleast_1d(z)
    if z.size == 0:
        return z, z
    elif z.ndim != 1:
        raise ValueError('_cplxreal only accepts 1-D input')

    if tol is None:
        # Get tolerance from dtype of input
        tol = 100 * np.finfo((1.0 * z).dtype).eps

    # Sort by real part, magnitude of imaginary part (speed up further sorting)
    z = z[np.lexsort((abs(z.imag), z.real))]

    # Split reals from conjugate pairs
    real_indices = abs(z.imag) <= tol * abs(z)
    zr = z[real_indices].real

    if len(zr) == len(z):
        # Input is entirely real
        return np.array([]), zr

    # Split positive and negative halves of conjugates
    z = z[~real_indices]
    zp = z[z.imag > 0]
    zn = z[z.imag < 0]

    if len(zp) != len(zn):
        raise ValueError('Array contains complex value with no matching '
                         'conjugate.')

    # Find runs of (approximately) the same real part
    same_real = np.diff(zp.real) <= tol * abs(zp[:-1])
    diffs = np.diff(np.concatenate(([0], same_real, [0])))
    run_starts = np.nonzero(diffs > 0)[0]
    run_stops = np.nonzero(diffs < 0)[0]

    # Sort each run by their imaginary parts
    for i in range(len(run_starts)):
        start = run_starts[i]
        stop = run_stops[i] + 1
        for chunk in (zp[start:stop], zn[start:stop]):
            chunk[...] = chunk[np.lexsort([abs(chunk.imag)])]

    # Check that negatives match positives
    if any(abs(zp - zn.conj()) > tol * abs(zn)):
        raise ValueError('Array contains complex value with no matching '
                         'conjugate.')

    # Average out numerical inaccuracy in real vs imag parts of pairs
    zc = (zp + zn.conj()) / 2

    return zc, zr

def _one_sos2tf(mySOS):
    """
    
    Parameters
    ----------
    tfa : TYPE
        DESCRIPTION.
    tfb : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    Example
    -------

    """
    
    # check zeros in the higher order coerffs
    if mySOS[0] == 0 and mySOS[1] == 0:
        num = mySOS[2]
    elif mySOS[0] == 0:
        num = mySOS[1:3]
    else:
        num = mySOS[:3]
        
    if mySOS[3] == 0 and mySOS[4] == 0:
        den = mySOS[-1]
    elif mySOS[3] == 0:
        den = mySOS[4:]
    else:
        den = mySOS[3:]
    
    return num, den

def _build_poly_str(this_poly):
    """
    
    Parameters
    ----------
    tfa : TYPE
        DESCRIPTION.
    tfb : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    Example
    -------

    """
    
    poly_str = ''

    for ii in range( this_poly.shape[0] ):
    
        if this_poly[ii] != 0.0:
            
            if (this_poly.shape[0]-2) == ii:
                poly_str +=  '+ s ' 
            
            elif (this_poly.shape[0]-1) != ii:
                poly_str +=  '+ s^{:d} '.format(this_poly.shape[0]-ii-1) 

            if (this_poly.shape[0]-1) == ii:
                poly_str += '+ {:3.4g} '.format(this_poly[ii])
            else:
                if this_poly[ii] != 1.0:
                    poly_str +=  '\,\, {:3.4g} '.format(this_poly[ii])
                
    return poly_str[2:]

def _build_omegayq_str(this_quad_poly, den = np.array([])):
    """
    
    Parameters
    ----------
    tfa : TYPE
        DESCRIPTION.
    tfb : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    Example
    -------

    """

    if den.shape[0] > 0:
        # numerator style bandpass s. hh . oemga/ qq
        
        omega = np.sqrt(den[2]) # from denominator
        qq = omega / den[1] # from denominator
        
        hh = this_quad_poly[1] * qq / omega
        
        poly_str = r's\,{:3.4g}\,\frac{{{:3.4g}}}{{{:3.4g}}}'.format(hh, omega, qq )
    
    else:
        # all other complete quadratic polynomial
        omega = np.sqrt(this_quad_poly[2])
        
        if this_quad_poly[1] == 0:
            poly_str = r's^2 + {:3.4g}^2'.format(omega)
        else:
            qq = omega / this_quad_poly[1]
            poly_str = r's^2 + s \frac{{{:3.4g}}}{{{:3.4g}}} + {:3.4g}^2'.format(omega, qq, omega)
        
                
    return poly_str

def _complementaryColor(my_hex):
    """Returns complementary RGB color

    Example:
    >>>complementaryColor('FFFFFF')
    '000000'
    """
    
    if my_hex[0] == '#':
        my_hex = my_hex[1:]
    rgb = (my_hex[0:2], my_hex[2:4], my_hex[4:6])
    comp = ['%02X' % (255 - int(a, 16)) for a in rgb]
    return '#' + ''.join(comp)
